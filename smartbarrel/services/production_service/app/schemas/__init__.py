from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class BlockResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None


class WellResponse(BaseModel):
    id: UUID
    code: str
    block_id: UUID
    pump_type: str | None
    is_active: bool


class DailyProductionCreate(BaseModel):
    date: date
    block_code: str
    well_code: str | None = None
    wells_total: int = Field(ge=0)
    wells_active: int = Field(ge=0)
    oil_bbl: float = Field(ge=0)
    water_bbl: float = Field(ge=0)
    watercut_pct: float = Field(ge=0, le=100)


class DailyProductionResponse(BaseModel):
    id: UUID
    date: date
    block: str
    well: str | None
    wells_total: int
    wells_active: int
    oil_bbl: float
    water_bbl: float
    watercut_pct: float
    wor: float | None


class KpiResponse(BaseModel):
    period: str
    production_total_bbl: float
    production_avg_bbl_day: float
    watercut_avg_pct: float
    active_wells_avg: float
    delta_vs_previous_pct: float | None
