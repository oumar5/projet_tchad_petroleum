import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..models import EtlRun, EtlSnapshot
from ..services.excel_ingestor import file_sha256, ingest_excel
from ..services.sheet_detector import analyze_workbook
from .deps import get_db

router = APIRouter(prefix="/v1/etl", tags=["etl"])


def _storage_key(filename: str, digest: str) -> str:
    """Stable storage key — `imports/{first8_hash}_{filename}`."""
    safe = filename.replace("/", "_").replace("\\", "_")
    return f"imports/{digest[:12]}_{safe}"


async def _persist_upload(
    request: Request,
    upload: UploadFile,
    session: AsyncSession,
    label: str | None,
) -> tuple[EtlSnapshot, bytes, str]:
    """Read upload bytes once, store via StorageBackend, create snapshot."""
    if upload.filename is None:
        raise HTTPException(400, "Missing filename")

    contents = await upload.read()
    if not contents:
        raise HTTPException(422, "Fichier vide.")

    digest = hashlib.sha256(contents).hexdigest()
    storage_key = _storage_key(upload.filename, digest)
    storage = request.app.state.storage
    storage.put(
        key=storage_key,
        data=contents,
        content_type=(
            upload.content_type
            or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )

    # Snapshots.label is UNIQUE — suffix with a UTC timestamp so re-uploads
    # of the same file do not collide.
    if label is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        label = f"upload-{digest[:8]}-{ts}"

    snapshot = EtlSnapshot(
        label=label,
        source_type="excel",
        source_uri=storage_key,
        file_hash=digest,
    )
    session.add(snapshot)
    await session.flush()
    return snapshot, contents, storage_key


def _bytes_to_tmp_path(contents: bytes, suffix: str = ".xlsx") -> Path:
    fh = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        fh.write(contents)
        fh.flush()
    finally:
        fh.close()
    return Path(fh.name)


# ---------------------------------------------------------------------------
# 1. INSPECT — analyse d'un fichier Excel sans toucher la BDD
# ---------------------------------------------------------------------------


@router.post("/inspect/excel")
async def inspect_excel_endpoint(
    upload: UploadFile,
    user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    label: str | None = None,
) -> dict:
    """Analyse un fichier Excel : retourne par onglet le type détecté, la cible
    et un aperçu, sans rien insérer en BDD. Le fichier est stocké via le
    StorageBackend pour permettre l'ingestion sélective ensuite via
    `POST /v1/etl/ingest/excel/selective`.
    """
    snapshot, contents, storage_key = await _persist_upload(
        request, upload, session, label
    )

    tmp_path = _bytes_to_tmp_path(contents)
    try:
        analyses = analyze_workbook(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "snapshot_id": str(snapshot.id),
        "storage_key": storage_key,
        "file_hash": snapshot.file_hash,
        "filename": upload.filename,
        "label": snapshot.label,
        "size_bytes": len(contents),
        "sheets": [a.to_dict() for a in analyses],
        "uploaded_by": user.id,
    }


# ---------------------------------------------------------------------------
# 2. SELECTIVE INGEST — ingère uniquement les onglets cochés
# ---------------------------------------------------------------------------


class SelectiveIngestRequest(BaseModel):
    snapshot_id: UUID
    sheets: list[str]  # detected_kind values to ingest, e.g. ['daily_production']


@router.post("/ingest/excel/selective")
async def ingest_selective_endpoint(
    body: SelectiveIngestRequest,
    user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Ingère uniquement les onglets demandés depuis un snapshot précédemment
    uploadé via `/inspect/excel`. Pour le moment, seul `daily_production` est
    réellement supporté (sprint 1) ; les autres types renverront `skipped: true`.
    """
    snapshot = await session.get(EtlSnapshot, body.snapshot_id)
    if snapshot is None:
        raise HTTPException(404, "Snapshot inconnu — relance /inspect/excel.")

    storage = request.app.state.storage
    if not storage.exists(snapshot.source_uri):
        raise HTTPException(
            410, "Fichier source absent du stockage — relance /inspect/excel."
        )

    body_stream = storage.open(snapshot.source_uri)
    try:
        contents = body_stream.read()
    finally:
        close = getattr(body_stream, "close", None)
        if callable(close):
            close()

    tmp_path = _bytes_to_tmp_path(contents)
    try:
        analyses = analyze_workbook(tmp_path)
        analyses_by_kind = {a.detected_kind: a for a in analyses}

        run = EtlRun(snapshot_id=snapshot.id, status="running")
        session.add(run)
        await session.flush()

        per_sheet_results: list[dict] = []
        total_processed = 0
        total_skipped = 0
        total_failed = 0
        any_failure = False

        for kind in body.sheets:
            analysis = analyses_by_kind.get(kind)
            if analysis is None:
                per_sheet_results.append({
                    "kind": kind, "status": "skipped",
                    "reason": "Onglet introuvable dans le fichier.",
                    "rows_processed": 0, "rows_skipped": 0, "rows_failed": 0,
                })
                continue

            if kind == "daily_production":
                sp = await session.begin_nested()
                try:
                    result = await ingest_excel(session, tmp_path)
                    await sp.commit()
                    per_sheet_results.append({
                        "kind": kind, "sheet_name": analysis.name,
                        "status": "success",
                        "rows_processed": result.rows_processed,
                        "rows_skipped": result.rows_skipped,
                        "rows_failed": result.rows_failed,
                    })
                    total_processed += result.rows_processed
                    total_skipped += result.rows_skipped
                    total_failed += result.rows_failed
                except Exception as exc:
                    await sp.rollback()
                    any_failure = True
                    per_sheet_results.append({
                        "kind": kind, "sheet_name": analysis.name,
                        "status": "failed", "error": str(exc),
                        "rows_processed": 0, "rows_skipped": 0,
                        "rows_failed": 0,
                    })
            elif analysis.ready:
                # Reserved for sprint 2 ingestors registered against `kind`.
                per_sheet_results.append({
                    "kind": kind, "sheet_name": analysis.name,
                    "status": "skipped",
                    "reason": "Ingestor pas encore implémenté.",
                    "rows_processed": 0, "rows_skipped": 0, "rows_failed": 0,
                })
            else:
                per_sheet_results.append({
                    "kind": kind, "sheet_name": analysis.name,
                    "status": "skipped",
                    "reason": "Onglet pas encore supporté (sprint 2).",
                    "rows_processed": 0, "rows_skipped": 0, "rows_failed": 0,
                })

        run.status = "failed" if any_failure else "success"
        run.rows_processed = total_processed
        run.rows_skipped = total_skipped
        run.rows_failed = total_failed
        run.finished_at = datetime.now(timezone.utc)
        snapshot.row_counts = {
            "production_inserted": total_processed,
            "production_skipped": total_skipped,
            "production_failed": total_failed,
            "sheets": per_sheet_results,
        }
    finally:
        tmp_path.unlink(missing_ok=True)

    publisher = getattr(request.app.state, "publisher", None)
    if publisher is not None and total_processed > 0:
        try:
            await publisher.publish(
                "data.ingested.production",
                {
                    "snapshot_id": str(snapshot.id),
                    "label": snapshot.label,
                    "rows": total_processed,
                    "triggered_by": user.id,
                },
            )
        except Exception:
            pass

    return {
        "snapshot_id": str(snapshot.id),
        "run_id": str(run.id),
        "status": run.status,
        "sheets": per_sheet_results,
        "totals": {
            "rows_processed": total_processed,
            "rows_skipped": total_skipped,
            "rows_failed": total_failed,
        },
    }


# ---------------------------------------------------------------------------
# 3. LEGACY full-file ingest (kept for backward compat — production sheet only)
# ---------------------------------------------------------------------------


@router.post("/ingest/excel", status_code=202)
async def ingest_excel_endpoint(
    upload: UploadFile,
    _user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    label: str | None = None,
) -> dict:
    snapshot, contents, _ = await _persist_upload(request, upload, session, label)
    tmp_path = _bytes_to_tmp_path(contents)

    run = EtlRun(snapshot_id=snapshot.id, status="running")
    session.add(run)
    await session.flush()

    try:
        result = await ingest_excel(session, tmp_path)
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
    finally:
        tmp_path.unlink(missing_ok=True)

    publisher = getattr(request.app.state, "publisher", None)
    if publisher is not None:
        try:
            await publisher.publish(
                "data.ingested.production",
                {"snapshot_id": str(snapshot.id), "label": snapshot.label,
                 "rows": result.rows_processed},
            )
        except Exception:
            pass

    return {
        "snapshot_id": str(snapshot.id),
        "run_id": str(run.id),
        "status": run.status,
        "rows_processed": run.rows_processed,
        "rows_skipped": run.rows_skipped,
        "rows_failed": run.rows_failed,
    }


# ---------------------------------------------------------------------------
# 4. Runs — listing + detail (unchanged)
# ---------------------------------------------------------------------------


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


# Keep legacy import resolution for `file_sha256` symbol used by tests.
_ = file_sha256
