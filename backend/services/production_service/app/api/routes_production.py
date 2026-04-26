"""Production endpoints."""
import csv
import io
from datetime import date as Date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..models import Block, DailyProduction, Well
from ..schemas import (
    BlockResponse, DailyProductionCreate, DailyProductionResponse, KpiResponse,
    WellResponse,
)
from .deps import get_db

router = APIRouter(prefix="/v1/production", tags=["production"])


@router.get("/blocks", response_model=list[BlockResponse])
async def list_blocks(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[BlockResponse]:
    rows = list((await session.execute(select(Block).order_by(Block.code))).scalars())
    return [BlockResponse(id=b.id, code=b.code, name=b.name, description=b.description)
            for b in rows]


@router.get("/wells", response_model=list[WellResponse])
async def list_wells(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    block: str | None = None,
) -> list[WellResponse]:
    stmt = select(Well).order_by(Well.code)
    if block is not None:
        stmt = stmt.join(Block).where(Block.code == block)
    rows = list((await session.execute(stmt)).scalars())
    return [
        WellResponse(id=w.id, code=w.code, block_id=w.block_id,
                     pump_type=w.pump_type, is_active=w.is_active)
        for w in rows
    ]


@router.get("/daily")
async def list_daily(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_: Date = Query(default=None, alias="from"),
    to: Date | None = None,
    block: str | None = None,
    page: int = 1,
    page_size: int = Query(default=100, le=1000),
) -> dict:
    stmt = select(DailyProduction, Block).join(Block, DailyProduction.block_id == Block.id)
    if from_ is not None:
        stmt = stmt.where(DailyProduction.date >= from_)
    if to is not None:
        stmt = stmt.where(DailyProduction.date <= to)
    if block is not None:
        stmt = stmt.where(Block.code == block)
    stmt = stmt.order_by(DailyProduction.date.desc())
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = (await session.execute(stmt)).all()
    items = [
        {
            "id": str(dp.id), "date": dp.date.isoformat(), "block": b.code,
            "wells_total": dp.wells_total, "wells_active": dp.wells_active,
            "oil_bbl": float(dp.oil_bbl), "water_bbl": float(dp.water_bbl),
            "watercut_pct": float(dp.watercut_pct),
            "wor": float(dp.wor) if dp.wor is not None else None,
        } for dp, b in rows
    ]
    return {"items": items, "page": page, "page_size": page_size}


@router.post("/daily", status_code=201)
async def create_daily(
    body: DailyProductionCreate,
    user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    block = (await session.execute(
        select(Block).where(Block.code == body.block_code)
    )).scalar_one_or_none()
    if block is None:
        raise HTTPException(404, f"Block '{body.block_code}' not found")

    well_id: UUID | None = None
    if body.well_code:
        well = (await session.execute(
            select(Well).where(Well.code == body.well_code)
        )).scalar_one_or_none()
        if well is None:
            raise HTTPException(404, f"Well '{body.well_code}' not found")
        well_id = well.id

    wor = body.water_bbl / body.oil_bbl if body.oil_bbl > 0 else None
    dp = DailyProduction(
        date=body.date, block_id=block.id, well_id=well_id,
        wells_total=body.wells_total, wells_active=body.wells_active,
        oil_bbl=body.oil_bbl, water_bbl=body.water_bbl,
        watercut_pct=body.watercut_pct, wor=wor,
        source="manual", created_by=UUID(user.id),
    )
    session.add(dp)
    await session.flush()
    return {"id": str(dp.id)}


@router.get("/kpis", response_model=KpiResponse)
async def kpis(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    period: str = "30d",
) -> KpiResponse:
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period)
    if days is None:
        raise HTTPException(400, "period must be 7d|30d|90d|1y")

    end = Date.today()
    start = end - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    cur_stmt = select(
        func.coalesce(func.sum(DailyProduction.oil_bbl), 0),
        func.coalesce(func.avg(DailyProduction.watercut_pct), 0),
        func.coalesce(func.avg(DailyProduction.wells_active), 0),
        func.count(),
    ).where(DailyProduction.date.between(start, end))
    cur_total, cur_wc, cur_wells, cur_count = (await session.execute(cur_stmt)).one()

    prev_stmt = select(func.coalesce(func.sum(DailyProduction.oil_bbl), 0)).where(
        DailyProduction.date.between(prev_start, start - timedelta(days=1))
    )
    prev_total = float((await session.execute(prev_stmt)).scalar_one() or 0)

    delta = None
    if prev_total > 0:
        delta = ((float(cur_total) - prev_total) / prev_total) * 100

    avg_day = float(cur_total) / cur_count if cur_count else 0
    return KpiResponse(
        period=period, production_total_bbl=float(cur_total),
        production_avg_bbl_day=avg_day, watercut_avg_pct=float(cur_wc),
        active_wells_avg=float(cur_wells), delta_vs_previous_pct=delta,
    )


@router.get("/export")
async def export_data(
    _: Annotated[CurrentUser, Depends(require_permission("production:export"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    format: str = "csv",
    from_: Date | None = Query(default=None, alias="from"),
    to: Date | None = None,
) -> Response:
    if format != "csv":
        raise HTTPException(400, "Only csv supported in v1")
    stmt = select(DailyProduction, Block).join(Block, DailyProduction.block_id == Block.id)
    if from_:
        stmt = stmt.where(DailyProduction.date >= from_)
    if to:
        stmt = stmt.where(DailyProduction.date <= to)
    stmt = stmt.order_by(DailyProduction.date)
    rows = (await session.execute(stmt)).all()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "block", "wells_total", "wells_active",
                "oil_bbl", "water_bbl", "watercut_pct", "wor"])
    for dp, b in rows:
        w.writerow([
            dp.date.isoformat(), b.code, dp.wells_total, dp.wells_active,
            float(dp.oil_bbl), float(dp.water_bbl),
            float(dp.watercut_pct), float(dp.wor) if dp.wor else "",
        ])
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=production.csv"},
    )
