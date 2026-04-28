import contextlib
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..core.settings import get_settings
from ..models import MLJob, MLModel, MLPrediction
from ..schemas import (
    JobResponse,
    ModelResponse,
    PredictForecastRequest,
    PredictionResponse,
    PredictMaintenanceRequest,
    PredictWaterRequest,
    TrainRequest,
)
from .deps import get_db

router = APIRouter(prefix="/v1/ml", tags=["ml"])


def _serialize_model(m: MLModel) -> dict:
    return {
        "id": str(m.id),
        "name": m.name,
        "version": m.version,
        "algorithm": m.algorithm,
        "trained_at": m.trained_at.isoformat(),
    }


async def _publish(request: Request, routing_key: str, payload: dict) -> None:
    publisher = getattr(request.app.state, "publisher", None)
    if publisher is not None:
        with contextlib.suppress(Exception):
            await publisher.publish(routing_key, payload)


# ---------------------------------------------------------------------------
# Real predict endpoints — no more stubs
# ---------------------------------------------------------------------------

@router.post("/predict/maintenance", response_model=PredictionResponse)
async def predict_maintenance(
    body: PredictMaintenanceRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    settings = get_settings()
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "maintenance")
    )

    result = await _run_in_thread(
        inference.predict_maintenance,
        model_record,
        settings.database_url,
        block=body.block,
        horizon_days=body.horizon_days,
    )

    pred = MLPrediction(
        model_id=model_record.id,
        prediction_type="maintenance",
        input_data=body.model_dump(mode="json"),
        output_data=result,
        confidence=result.get("confidence"),
        requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()
    await _publish(request, "prediction.completed", {
        "prediction_id": str(pred.id),
        "type": "maintenance",
        "model_id": str(model_record.id),
        "block": body.block,
    })

    return PredictionResponse(
        predictions=result["predictions"],
        model=_serialize_model(model_record),
        confidence=result.get("confidence"),
    )


@router.post("/predict/forecast", response_model=PredictionResponse)
async def predict_forecast(
    body: PredictForecastRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    settings = get_settings()
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "forecast")
    )

    result = await _run_in_thread(
        inference.predict_forecast,
        model_record,
        settings.database_url,
        horizon_days=body.horizon_days,
    )

    pred = MLPrediction(
        model_id=model_record.id,
        prediction_type="forecast",
        input_data=body.model_dump(mode="json"),
        output_data={"horizon_days": body.horizon_days, "n_points": len(result["predictions"])},
        confidence=result.get("confidence"),
        requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()
    await _publish(request, "prediction.completed", {
        "prediction_id": str(pred.id),
        "type": "forecast",
        "model_id": str(model_record.id),
    })

    return PredictionResponse(
        predictions=result["predictions"],
        model=_serialize_model(model_record),
        confidence=result.get("confidence"),
    )


@router.post("/predict/water", response_model=PredictionResponse)
async def predict_water(
    body: PredictWaterRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    settings = get_settings()
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "water")
    )

    result = await _run_in_thread(
        inference.predict_water,
        model_record,
        settings.database_url,
        block=body.block,
        target_oil_bbl=body.target_oil_bbl,
    )

    pred = MLPrediction(
        model_id=model_record.id,
        prediction_type="water",
        input_data=body.model_dump(mode="json"),
        output_data=result,
        confidence=result.get("confidence"),
        requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()
    await _publish(request, "prediction.completed", {
        "prediction_id": str(pred.id),
        "type": "water",
        "model_id": str(model_record.id),
        "block": body.block,
    })

    return PredictionResponse(
        predictions=result["predictions"],
        model=_serialize_model(model_record),
        confidence=result.get("confidence"),
    )


async def _run_in_thread(fn, *args, **kwargs):
    """Run a sync inference call (blocking pandas/joblib) off the event loop."""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ---------------------------------------------------------------------------
# Train (queues a Celery job — see workers/celery_app.py for the real pipeline)
# ---------------------------------------------------------------------------

@router.post("/train", response_model=JobResponse, status_code=202)
async def train(
    body: TrainRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:train"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    job = MLJob(
        job_type="train", model_type=body.model_type, algorithm=body.algorithm,
        status="queued", params=body.params, requested_by=UUID(user.id),
    )
    session.add(job)
    await session.flush()

    from ..workers.celery_app import train_task
    train_task.delay(str(job.id), body.model_type, body.algorithm, body.params)
    await _publish(request, "model.trained", {
        "job_id": str(job.id), "model_type": body.model_type,
        "algorithm": body.algorithm, "status": "queued",
    })

    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("ml:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    job = await session.get(MLJob, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return {
        "id": str(job.id), "status": job.status, "job_type": job.job_type,
        "model_type": job.model_type, "algorithm": job.algorithm,
        "result": job.result, "error": job.error,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    _: Annotated[CurrentUser, Depends(require_permission("ml:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    type: str | None = None,
    active: bool | None = None,
) -> list[ModelResponse]:
    stmt = select(MLModel).order_by(MLModel.trained_at.desc())
    if type:
        stmt = stmt.where(MLModel.model_type == type)
    if active is not None:
        stmt = stmt.where(MLModel.is_active == active)
    rows = list((await session.execute(stmt)).scalars())
    return [
        ModelResponse(
            id=m.id, name=m.name, version=m.version, model_type=m.model_type,
            algorithm=m.algorithm, metrics=m.metrics, is_active=m.is_active,
            trained_at=m.trained_at,
        ) for m in rows
    ]


@router.patch("/models/{model_id}/activate", status_code=204)
async def activate_model(
    model_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("ml:train"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    target = await session.get(MLModel, model_id)
    if target is None:
        raise HTTPException(404, "Model not found")
    others = (await session.execute(
        select(MLModel).where(
            MLModel.model_type == target.model_type, MLModel.id != target.id,
        )
    )).scalars()
    for o in others:
        o.is_active = False
    target.is_active = True


@router.get("/predictions/history")
async def predictions_history(
    _: Annotated[CurrentUser, Depends(require_permission("ml:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    type: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    stmt = select(MLPrediction).order_by(MLPrediction.created_at.desc())
    if type:
        stmt = stmt.where(MLPrediction.prediction_type == type)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = list((await session.execute(stmt)).scalars())
    return {
        "items": [{
            "id": str(p.id),
            "prediction_type": p.prediction_type,
            "model_id": str(p.model_id),
            "created_at": p.created_at.isoformat(),
            "confidence": float(p.confidence) if p.confidence else None,
        } for p in rows],
        "page": page, "page_size": page_size,
    }
