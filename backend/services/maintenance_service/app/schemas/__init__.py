from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FailureCreate(BaseModel):
    notification_date: date
    block: str
    equipment_code: str | None = None
    failure_type: str
    severity: str = Field(pattern=r"^(low|medium|high|critical)$")
    description: str | None = None
    estimated_duration_h: int | None = None


class FailureResponse(BaseModel):
    id: UUID
    notification_date: date
    block: str
    failure_type: str
    severity: str
    description: str | None
    resolved_at: str | None


class InterventionCreate(BaseModel):
    failure_id: UUID | None = None
    intervention_date: date
    intervention_type: str
    duration_h: float | None = None
    result: str | None = None
    cost: float | None = None
    notes: str | None = None


class InterventionResponse(BaseModel):
    id: UUID
    failure_id: UUID | None
    intervention_date: date
    intervention_type: str
    duration_h: float | None
    result: str | None
