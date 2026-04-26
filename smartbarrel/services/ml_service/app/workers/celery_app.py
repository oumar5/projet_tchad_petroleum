"""Celery worker for async ML training jobs."""
from celery import Celery

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
    task_time_limit=60 * 60,  # 1h hard timeout
)


@celery_app.task(name="ml.train", bind=True)
def train_task(self, job_id: str, model_type: str, algorithm: str, params: dict) -> dict:
    """Synchronous training task.

    In production this should:
      1. Read snapshot from etl-service
      2. Train the model
      3. Persist to disk + register in ml.models
      4. Update ml.jobs status
    """
    from datetime import datetime, timezone
    return {
        "job_id": job_id,
        "model_type": model_type,
        "algorithm": algorithm,
        "params": params,
        "status": "stub",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {"placeholder": True},
    }
