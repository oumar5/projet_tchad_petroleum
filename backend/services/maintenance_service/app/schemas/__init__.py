from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FailureCreate(BaseModel):
    notification_date: date
    block: str
    well_code: str | None = None
    equipment_code: str | None = None
    failure_type: str
    severity: str = Field(pattern=r"^(low|medium|high|critical)$")
    description: str | None = None
    estimated_duration_h: int | None = None


class FailureUpdate(BaseModel):
    status: str | None = Field(
        default=None, pattern=r"^(pending|in_progress|resolved|cancelled)$"
    )
    severity: str | None = Field(
        default=None, pattern=r"^(low|medium|high|critical)$"
    )
    assigned_to: UUID | None = None
    description: str | None = None
    repair_cost: float | None = None
    resolved_at: datetime | None = None


class FailureResponse(BaseModel):
    id: UUID
    notification_date: date
    block: str
    well_code: str | None = None
    failure_type: str
    severity: str
    status: str
    assigned_to: UUID | None = None
    description: str | None
    resolved_at: datetime | None = None


class InterventionCreate(BaseModel):
    failure_id: UUID | None = None
    intervention_date: date
    intervention_type: str
    duration_h: float | None = None
    result: str | None = None
    cost: float | None = None
    notes: str | None = None


class InterventionUpdate(BaseModel):
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


class AttachmentResponse(BaseModel):
    id: UUID
    failure_id: UUID | None = None
    intervention_id: UUID | None = None
    filename: str
    mime_type: str
    size_bytes: int
    storage_path: str
    uploaded_by: UUID
    created_at: datetime
