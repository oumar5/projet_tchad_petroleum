import contextlib
import uuid as _uuid
from datetime import date as Date
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..models import Attachment, Equipment, Failure, Intervention
from ..schemas import (
    AttachmentResponse,
    FailureCreate,
    FailureResponse,
    FailureUpdate,
    InterventionCreate,
    InterventionResponse,
    InterventionUpdate,
)
from .deps import get_db

router = APIRouter(prefix="/v1/maintenance", tags=["maintenance"])


_ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "application/pdf",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _failure_to_response(f: Failure) -> FailureResponse:
    return FailureResponse(
        id=f.id,
        notification_date=f.notification_date,
        block=f.block,
        well_code=f.well_code,
        failure_type=f.failure_type,
        severity=f.severity,
        status=f.status,
        assigned_to=f.assigned_to,
        description=f.description,
        resolved_at=f.resolved_at,
    )


async def _publish(request: Request, routing_key: str, payload: dict) -> None:
    publisher = getattr(request.app.state, "publisher", None)
    if publisher is not None:
        with contextlib.suppress(Exception):
            await publisher.publish(routing_key, payload)


# ---------------------------------------------------------------------------
# Failures
# ---------------------------------------------------------------------------


@router.get("/failures", response_model=list[FailureResponse])
async def list_failures(
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_: Date | None = Query(default=None, alias="from"),
    to: Date | None = None,
    block: str | None = None,
    status: str | None = Query(default=None, pattern=r"^(pending|in_progress|resolved|cancelled)$"),
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
    if status:
        stmt = stmt.where(Failure.status == status)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = list((await session.execute(stmt)).scalars())
    return [_failure_to_response(f) for f in rows]


@router.get("/failures/{failure_id}", response_model=FailureResponse)
async def get_failure(
    failure_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FailureResponse:
    f = await session.get(Failure, failure_id)
    if f is None:
        raise HTTPException(404, "Failure not found")
    return _failure_to_response(f)


@router.post("/failures", response_model=FailureResponse, status_code=201)
async def create_failure(
    body: FailureCreate,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    request: Request,
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
        notification_date=body.notification_date,
        block=body.block,
        well_code=body.well_code,
        equipment_id=equipment_id,
        failure_type=body.failure_type,
        severity=body.severity,
        description=body.description,
        estimated_duration_h=body.estimated_duration_h,
        reported_by=UUID(user.id),
        status="pending",
    )
    session.add(f)
    await session.flush()

    if body.severity in ("high", "critical"):
        await _publish(request, "alert.failure_reported", {
            "failure_id": str(f.id),
            "block": f.block,
            "well_code": f.well_code,
            "severity": f.severity,
            "failure_type": f.failure_type,
            "reported_by": user.id,
        })

    return _failure_to_response(f)


@router.patch("/failures/{failure_id}", response_model=FailureResponse)
async def update_failure(
    failure_id: UUID,
    body: FailureUpdate,
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FailureResponse:
    f = await session.get(Failure, failure_id)
    if f is None:
        raise HTTPException(404, "Failure not found")

    previous_status = f.status
    data = body.model_dump(exclude_unset=True)

    if "status" in data:
        f.status = data["status"]
        if data["status"] == "resolved" and f.resolved_at is None:
            f.resolved_at = datetime.now(timezone.utc)
        if data["status"] != "resolved":
            # if reopening, drop resolved_at unless caller set it explicitly
            if "resolved_at" not in data:
                f.resolved_at = None
    if "severity" in data:
        f.severity = data["severity"]
    if "assigned_to" in data:
        f.assigned_to = data["assigned_to"]
    if "description" in data:
        f.description = data["description"]
    if "repair_cost" in data:
        f.repair_cost = data["repair_cost"]
    if "resolved_at" in data:
        f.resolved_at = data["resolved_at"]

    f.last_updated_by = UUID(user.id)
    await session.flush()

    if previous_status != f.status:
        await _publish(request, "failure.status_changed", {
            "failure_id": str(f.id),
            "previous_status": previous_status,
            "new_status": f.status,
            "updated_by": user.id,
        })

    return _failure_to_response(f)


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------


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


@router.patch("/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: UUID,
    body: InterventionUpdate,
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InterventionResponse:
    i = await session.get(Intervention, intervention_id)
    if i is None:
        raise HTTPException(404, "Intervention not found")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(i, field, value)
    await session.flush()
    return InterventionResponse(
        id=i.id, failure_id=i.failure_id, intervention_date=i.intervention_date,
        intervention_type=i.intervention_type,
        duration_h=float(i.duration_h) if i.duration_h else None,
        result=i.result,
    )


# ---------------------------------------------------------------------------
# Attachments (photos / PDFs attached to a failure or an intervention)
# ---------------------------------------------------------------------------


def _attachment_to_response(a: Attachment) -> AttachmentResponse:
    return AttachmentResponse(
        id=a.id,
        failure_id=a.failure_id,
        intervention_id=a.intervention_id,
        filename=a.filename,
        mime_type=a.mime_type,
        size_bytes=a.size_bytes,
        storage_path=a.storage_path,
        uploaded_by=a.uploaded_by,
        created_at=a.created_at,
    )


async def _save_attachment(
    request: Request,
    *,
    upload: UploadFile,
    user: CurrentUser,
    session: AsyncSession,
    failure_id: UUID | None = None,
    intervention_id: UUID | None = None,
) -> Attachment:
    if upload.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            422, f"Type de fichier non supporté ({upload.content_type})."
        )
    raw = await upload.read()
    if len(raw) == 0:
        raise HTTPException(422, "Fichier vide.")
    if len(raw) > _MAX_BYTES:
        raise HTTPException(413, "Fichier > 10 MB.")

    base_dir = Path(request.app.state.attachments_dir)
    parent_dir = base_dir / (
        f"failures/{failure_id}" if failure_id else f"interventions/{intervention_id}"
    )
    parent_dir.mkdir(parents=True, exist_ok=True)
    safe_name = upload.filename or "upload"
    fid = _uuid.uuid4().hex[:8]
    path = parent_dir / f"{fid}_{safe_name}"
    path.write_bytes(raw)

    a = Attachment(
        failure_id=failure_id,
        intervention_id=intervention_id,
        filename=safe_name,
        mime_type=upload.content_type,
        size_bytes=len(raw),
        storage_path=str(path),
        uploaded_by=UUID(user.id),
    )
    session.add(a)
    await session.flush()
    return a


@router.post(
    "/failures/{failure_id}/attachments",
    response_model=AttachmentResponse,
    status_code=201,
)
async def upload_failure_attachment(
    failure_id: UUID,
    upload: Annotated[UploadFile, File(...)],
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AttachmentResponse:
    f = await session.get(Failure, failure_id)
    if f is None:
        raise HTTPException(404, "Failure not found")
    a = await _save_attachment(
        request, upload=upload, user=user, session=session, failure_id=failure_id
    )
    return _attachment_to_response(a)


@router.get(
    "/failures/{failure_id}/attachments",
    response_model=list[AttachmentResponse],
)
async def list_failure_attachments(
    failure_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AttachmentResponse]:
    rows = list((await session.execute(
        select(Attachment).where(Attachment.failure_id == failure_id)
        .order_by(Attachment.created_at.desc())
    )).scalars())
    return [_attachment_to_response(a) for a in rows]


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("maintenance:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    a = await session.get(Attachment, attachment_id)
    if a is None:
        raise HTTPException(404, "Attachment not found")
    if not Path(a.storage_path).exists():
        raise HTTPException(410, "Fichier supprimé du stockage.")
    return FileResponse(
        a.storage_path,
        media_type=a.mime_type,
        filename=a.filename,
    )


@router.post(
    "/interventions/{intervention_id}/attachments",
    response_model=AttachmentResponse,
    status_code=201,
)
async def upload_intervention_attachment(
    intervention_id: UUID,
    upload: Annotated[UploadFile, File(...)],
    user: Annotated[CurrentUser, Depends(require_permission("maintenance:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AttachmentResponse:
    i = await session.get(Intervention, intervention_id)
    if i is None:
        raise HTTPException(404, "Intervention not found")
    a = await _save_attachment(
        request, upload=upload, user=user, session=session,
        intervention_id=intervention_id,
    )
    return _attachment_to_response(a)
