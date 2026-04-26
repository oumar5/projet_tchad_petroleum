from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..core.settings import get_settings
from ..models import EtlRun, EtlSnapshot
from ..services.excel_ingestor import file_sha256, ingest_excel
from .deps import get_db

router = APIRouter(prefix="/v1/etl", tags=["etl"])


@router.post("/ingest/excel", status_code=202)
async def ingest_excel_endpoint(
    upload: UploadFile,
    user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    label: str | None = None,
) -> dict:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    if upload.filename is None:
        raise HTTPException(400, "Missing filename")
    target = upload_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{upload.filename}"
    contents = await upload.read()
    target.write_bytes(contents)

    digest = file_sha256(target)
    snapshot = EtlSnapshot(
        label=label or f"upload-{digest[:8]}",
        source_type="excel",
        source_uri=str(target),
        file_hash=digest,
    )
    session.add(snapshot)
    await session.flush()

    run = EtlRun(snapshot_id=snapshot.id, status="running")
    session.add(run)
    await session.flush()

    try:
        result = await ingest_excel(session, target)
        run.status = "success"
        run.rows_processed = result.rows_processed
        run.rows_skipped = result.rows_skipped
        run.rows_failed = result.rows_failed
        run.finished_at = datetime.now(timezone.utc)
        snapshot.row_counts = {
            "production_inserted": result.rows_processed,
            "production_skipped": result.rows_skipped,
            "production_failed": result.rows_failed,
        }
    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.finished_at = datetime.now(timezone.utc)
        raise HTTPException(500, f"Ingestion failed: {e}") from e

    publisher = getattr(request.app.state, "publisher", None)
    if publisher is not None:
        await publisher.publish(
            "data.ingested.production",
            {"snapshot_id": str(snapshot.id), "label": snapshot.label,
             "rows": result.rows_processed},
        )

    return {
        "snapshot_id": str(snapshot.id),
        "run_id": str(run.id),
        "status": run.status,
        "rows_processed": run.rows_processed,
        "rows_skipped": run.rows_skipped,
        "rows_failed": run.rows_failed,
    }


@router.get("/runs")
async def list_runs(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    stmt = select(EtlRun).order_by(EtlRun.started_at.desc())
    if status:
        stmt = stmt.where(EtlRun.status == status)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = list((await session.execute(stmt)).scalars())
    return {
        "items": [{
            "id": str(r.id), "snapshot_id": str(r.snapshot_id) if r.snapshot_id else None,
            "status": r.status, "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "rows_processed": r.rows_processed,
            "rows_failed": r.rows_failed,
        } for r in rows],
        "page": page, "page_size": page_size,
    }


@router.get("/runs/{run_id}")
async def get_run(
    run_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    run = await session.get(EtlRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return {
        "id": str(run.id), "status": run.status,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "rows_processed": run.rows_processed,
        "rows_skipped": run.rows_skipped,
        "rows_failed": run.rows_failed,
        "error": run.error_message,
    }
