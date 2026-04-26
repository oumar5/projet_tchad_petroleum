from datetime import date as Date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..models import Equipment, Failure, Intervention
from ..schemas import (
    FailureCreate,
    FailureResponse,
    InterventionCreate,
    InterventionResponse,
)
from .deps import get_db

router = APIRouter(prefix="/v1/maintenance", tags=["maintenance"])


@router.get("/failures", response_model=list[FailureResponse])
async def list_failures(
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_: Date | None = Query(default=None, alias="from"),
    to: Date | None = None,
    block: str | None = None,
    page: int = 1,
    page_size: int = Query(default=100, le=1000),
) -> list[FailureResponse]:
    stmt = select(Failure).order_by(Failure.notification_date.desc())
    if from_:
        stmt = stmt.where(Failure.notification_date >= from_)
    if to:
        stmt = stmt.where(Failure.notification_date <= to)
    if block:
        stmt = stmt.where(Failure.block == block)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = list((await session.execute(stmt)).scalars())
    return [
        FailureResponse(
            id=f.id, notification_date=f.notification_date, block=f.block,
            failure_type=f.failure_type, severity=f.severity, description=f.description,
            resolved_at=f.resolved_at.isoformat() if f.resolved_at else None,
        ) for f in rows
    ]


@router.post("/failures", response_model=FailureResponse, status_code=201)
async def create_failure(
    body: FailureCreate,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FailureResponse:
    equipment_id = None
    if body.equipment_code:
        eq = (await session.execute(
            select(Equipment).where(Equipment.code == body.equipment_code)
        )).scalar_one_or_none()
        if eq is None:
            raise HTTPException(404, f"Equipment '{body.equipment_code}' not found")
        equipment_id = eq.id

    f = Failure(
        notification_date=body.notification_date, block=body.block,
        equipment_id=equipment_id, failure_type=body.failure_type,
        severity=body.severity, description=body.description,
        estimated_duration_h=body.estimated_duration_h,
        reported_by=UUID(user.id),
    )
    session.add(f)
    await session.flush()
    return FailureResponse(
        id=f.id, notification_date=f.notification_date, block=f.block,
        failure_type=f.failure_type, severity=f.severity, description=f.description,
        resolved_at=None,
    )


@router.get("/interventions", response_model=list[InterventionResponse])
async def list_interventions(
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_: Date | None = Query(default=None, alias="from"),
    to: Date | None = None,
) -> list[InterventionResponse]:
    stmt = select(Intervention).order_by(Intervention.intervention_date.desc())
    if from_:
        stmt = stmt.where(Intervention.intervention_date >= from_)
    if to:
        stmt = stmt.where(Intervention.intervention_date <= to)
    rows = list((await session.execute(stmt)).scalars())
    return [
        InterventionResponse(
            id=i.id, failure_id=i.failure_id, intervention_date=i.intervention_date,
            intervention_type=i.intervention_type,
            duration_h=float(i.duration_h) if i.duration_h else None,
            result=i.result,
        ) for i in rows
    ]


@router.post("/interventions", response_model=InterventionResponse, status_code=201)
async def create_intervention(
    body: InterventionCreate,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InterventionResponse:
    i = Intervention(
        failure_id=body.failure_id, intervention_date=body.intervention_date,
        intervention_type=body.intervention_type, duration_h=body.duration_h,
        result=body.result, cost=body.cost, notes=body.notes,
        performed_by=UUID(user.id),
    )
    session.add(i)
    await session.flush()
    return InterventionResponse(
        id=i.id, failure_id=i.failure_id, intervention_date=i.intervention_date,
        intervention_type=i.intervention_type,
        duration_h=float(i.duration_h) if i.duration_h else None,
        result=i.result,
    )
