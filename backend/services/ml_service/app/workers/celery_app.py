"""Celery worker — runs real ML training synchronously inside the worker process."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from celery import Celery
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ..core.settings import get_settings

_settings = get_settings()

celery_app = Celery(
    "ml_service",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,
)


def _sync_engine():
    url = _settings.database_url.replace("+asyncpg", "+psycopg2")
    return create_engine(url, future=True)


def _next_version(session: Session, name: str) -> str:
    row = session.execute(
        text("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(version FROM 'v([0-9]+)') AS INT)), 0) + 1
            FROM ml.models WHERE name = :name
        """),
        {"name": name},
    ).scalar() or 1
    return f"v{int(row)}"


@celery_app.task(name="ml.train", bind=True)
def train_task(
    self,
    job_id: str,
    model_type: str,
    algorithm: str,
    params: dict,
) -> dict:
    """Run the real training pipeline and register the artefact in ml.models."""
    from ..services.training import train_for_type

    engine = _sync_engine()
    started_at = datetime.now(timezone.utc)

    with Session(engine) as session:
        session.execute(
            text("""
                UPDATE ml.jobs
                SET status = 'running', started_at = :ts
                WHERE id = :id
            """),
            {"id": job_id, "ts": started_at},
        )
        session.commit()

    try:
        result = train_for_type(
            model_type=model_type,
            algorithm=algorithm,
            params=params or {},
            database_url=_settings.database_url,
            models_dir=Path(_settings.models_dir),
        )
    except Exception as exc:
        with Session(engine) as session:
            session.execute(
                text("""
                    UPDATE ml.jobs
                    SET status = 'failed',
                        error  = :err,
                        finished_at = :ts
                    WHERE id = :id
                """),
                {"id": job_id, "err": str(exc), "ts": datetime.now(timezone.utc)},
            )
            session.commit()
        raise

    finished_at = datetime.now(timezone.utc)
    model_name = f"{model_type}_{algorithm}"

    with Session(engine) as session:
        version = _next_version(session, model_name)

        # Deactivate previous active models of the same type, then INSERT new one as active.
        session.execute(
            text(
                "UPDATE ml.models SET is_active = false WHERE model_type = :t AND is_active = true"
            ),
            {"t": model_type},
        )
        new_model_id = session.execute(
            text("""
                INSERT INTO ml.models (
                    name, version, model_type, algorithm, metrics,
                    hyperparameters, blob_url, is_active, trained_at
                ) VALUES (
                    :name, :version, :model_type, :algorithm, CAST(:metrics AS jsonb),
                    CAST(:hp AS jsonb), :blob, true, :trained_at
                )
                RETURNING id
            """),
            {
                "name": model_name,
                "version": version,
                "model_type": model_type,
                "algorithm": algorithm,
                "metrics": _json(result.metrics),
                "hp": _json(result.hyperparameters),
                "blob": str(result.blob_path),
                "trained_at": finished_at,
            },
        ).scalar()

        session.execute(
            text("""
                UPDATE ml.jobs
                SET status      = 'success',
                    finished_at = :ts,
                    result      = CAST(:res AS jsonb)
                WHERE id = :id
            """),
            {
                "id": job_id,
                "ts": finished_at,
                "res": _json({
                    "model_id": str(new_model_id),
                    "model_name": model_name,
                    "version": version,
                    "metrics": result.metrics,
                    "blob_path": str(result.blob_path),
                    "n_train": result.n_train,
                    "n_test": result.n_test,
                }),
            },
        )
        session.commit()

    return {
        "job_id": job_id,
        "status": "success",
        "model_id": str(new_model_id),
        "model_name": model_name,
        "version": version,
        "metrics": result.metrics,
        "trained_at": finished_at.isoformat(),
    }


def _json(obj) -> str:
    """Serialise a Python obj to a JSON string for parameter binding."""
    import json
    return json.dumps(obj, default=str)
