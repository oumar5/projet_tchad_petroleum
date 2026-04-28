from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ZoneResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None


class ZoneCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class BlockResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    zone_id: UUID


class BlockCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    zone_id: UUID


class BlockUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    zone_id: UUID | None = None


class WellResponse(BaseModel):
    id: UUID
    code: str
    block_id: UUID
    pump_type: str | None
    is_active: bool


class WellCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    block_id: UUID
    pump_type: str | None = None
    is_active: bool = True


class WellUpdate(BaseModel):
    block_id: UUID | None = None
    pump_type: str | None = None
    is_active: bool | None = None


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
