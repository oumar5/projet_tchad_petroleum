from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PredictMaintenanceRequest(BaseModel):
    block: str
    horizon_days: int = Field(default=30, ge=1, le=180)
    model_id: UUID | None = None


class PredictForecastRequest(BaseModel):
    target: str = "oil_bbl"
    horizon_days: int = Field(default=30, ge=1, le=180)
    algorithm: str = "xgboost"
    model_id: UUID | None = None


class PredictWaterRequest(BaseModel):
    block: str
    target_oil_bbl: float | None = None
    model_id: UUID | None = None


class PredictionResponse(BaseModel):
    predictions: list[dict[str, Any]]
    model: dict[str, Any]
    confidence: float | None = None


class TrainRequest(BaseModel):
    model_type: str
    algorithm: str
    params: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    job_id: UUID
    status: str
    created_at: datetime


class ModelResponse(BaseModel):
    id: UUID
    name: str
    version: str
    model_type: str
    algorithm: str
    metrics: dict
    is_active: bool
    trained_at: datetime
