from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..models import MLJob, MLModel, MLPrediction
from ..schemas import (
    JobResponse, ModelResponse, PredictForecastRequest, PredictMaintenanceRequest,
    PredictWaterRequest, PredictionResponse, TrainRequest,
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


@router.post("/predict/maintenance", response_model=PredictionResponse)
async def predict_maintenance(
    body: PredictMaintenanceRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "maintenance")
    )

    pred = MLPrediction(
        model_id=model_record.id, prediction_type="maintenance",
        input_data=body.model_dump(mode="json"),
        output_data={"stub": True, "horizon_days": body.horizon_days},
        confidence=0.85, requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()

    return PredictionResponse(
        predictions=[{
            "block": body.block, "horizon_days": body.horizon_days,
            "stub_prediction": True,
        }],
        model=_serialize_model(model_record),
        confidence=0.85,
    )


@router.post("/predict/forecast", response_model=PredictionResponse)
async def predict_forecast(
    body: PredictForecastRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "forecast")
    )
    pred = MLPrediction(
        model_id=model_record.id, prediction_type="forecast",
        input_data=body.model_dump(mode="json"),
        output_data={"stub": True}, requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()
    return PredictionResponse(
        predictions=[{"target": body.target, "horizon_days": body.horizon_days,
                      "stub_prediction": True}],
        model=_serialize_model(model_record),
    )


@router.post("/predict/water", response_model=PredictionResponse)
async def predict_water(
    body: PredictWaterRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:predict"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    inference = request.app.state.inference
    model_record = (
        await inference.get_model_by_id(session, body.model_id)
        if body.model_id
        else await inference.get_active_model(session, "water_injection")
    )
    pred = MLPrediction(
        model_id=model_record.id, prediction_type="water",
        input_data=body.model_dump(mode="json"),
        output_data={"stub": True}, requested_by=UUID(user.id),
    )
    session.add(pred)
    await session.flush()
    return PredictionResponse(
        predictions=[{"block": body.block, "stub_prediction": True}],
        model=_serialize_model(model_record),
    )


@router.post("/train", response_model=JobResponse, status_code=202)
async def train(
    body: TrainRequest,
    user: Annotated[CurrentUser, Depends(require_permission("ml:train"))],
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
    # Deactivate other models of same type
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
