"""Production endpoints."""
import csv
import io
from datetime import date as Date
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser, require_permission

from ..core.cache import KpiCache
from ..models import Block, DailyProduction, Well, Zone
from ..schemas import (
    BlockCreate,
    BlockResponse,
    BlockUpdate,
    DailyProductionCreate,
    KpiResponse,
    WellCreate,
    WellResponse,
    WellUpdate,
    ZoneCreate,
    ZoneResponse,
    ZoneUpdate,
)
from .deps import get_db

router = APIRouter(prefix="/v1/production", tags=["production"])


@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ZoneResponse]:
    rows = list((await session.execute(select(Zone).order_by(Zone.code))).scalars())
    return [
        ZoneResponse(id=z.id, code=z.code, name=z.name, description=z.description)
        for z in rows
    ]


@router.post("/zones", response_model=ZoneResponse, status_code=201)
async def create_zone(
    body: ZoneCreate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ZoneResponse:
    existing = (await session.execute(
        select(Zone).where(Zone.code == body.code)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, f"La zone '{body.code}' existe déjà.")
    zone = Zone(code=body.code, name=body.name, description=body.description)
    session.add(zone)
    await session.flush()
    return ZoneResponse(id=zone.id, code=zone.code, name=zone.name,
                        description=zone.description)


@router.patch("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: UUID,
    body: ZoneUpdate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ZoneResponse:
    zone = await session.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(404, "Zone introuvable.")
    if body.name is not None:
        zone.name = body.name
    if body.description is not None:
        zone.description = body.description
    await session.flush()
    return ZoneResponse(id=zone.id, code=zone.code, name=zone.name,
                        description=zone.description)


@router.delete("/zones/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    zone = await session.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(404, "Zone introuvable.")
    has_blocks = (await session.execute(
        select(func.count()).select_from(Block).where(Block.zone_id == zone_id)
    )).scalar_one()
    if has_blocks > 0:
        raise HTTPException(
            409,
            f"Impossible de supprimer : {has_blocks} bloc(s) sont rattachés à cette zone.",
        )
    await session.delete(zone)


@router.get("/blocks", response_model=list[BlockResponse])
async def list_blocks(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    zone: str | None = None,
) -> list[BlockResponse]:
    stmt = select(Block).order_by(Block.code)
    if zone is not None:
        stmt = stmt.join(Zone).where(Zone.code == zone)
    rows = list((await session.execute(stmt)).scalars())
    return [
        BlockResponse(
            id=b.id, code=b.code, name=b.name,
            description=b.description, zone_id=b.zone_id,
        )
        for b in rows
    ]


@router.post("/blocks", response_model=BlockResponse, status_code=201)
async def create_block(
    body: BlockCreate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BlockResponse:
    zone = await session.get(Zone, body.zone_id)
    if zone is None:
        raise HTTPException(404, "Zone parente introuvable.")
    existing = (await session.execute(
        select(Block).where(Block.code == body.code)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, f"Le bloc '{body.code}' existe déjà.")
    block = Block(
        code=body.code, name=body.name,
        description=body.description, zone_id=body.zone_id,
    )
    session.add(block)
    await session.flush()
    return BlockResponse(
        id=block.id, code=block.code, name=block.name,
        description=block.description, zone_id=block.zone_id,
    )


@router.patch("/blocks/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: UUID,
    body: BlockUpdate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BlockResponse:
    block = await session.get(Block, block_id)
    if block is None:
        raise HTTPException(404, "Bloc introuvable.")
    if body.name is not None:
        block.name = body.name
    if body.description is not None:
        block.description = body.description
    if body.zone_id is not None:
        zone = await session.get(Zone, body.zone_id)
        if zone is None:
            raise HTTPException(404, "Zone parente introuvable.")
        block.zone_id = body.zone_id
    await session.flush()
    return BlockResponse(
        id=block.id, code=block.code, name=block.name,
        description=block.description, zone_id=block.zone_id,
    )


@router.delete("/blocks/{block_id}", status_code=204)
async def delete_block(
    block_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    block = await session.get(Block, block_id)
    if block is None:
        raise HTTPException(404, "Bloc introuvable.")
    in_use = (await session.execute(
        select(func.count()).select_from(DailyProduction).where(
            DailyProduction.block_id == block_id
        )
    )).scalar_one()
    if in_use > 0:
        raise HTTPException(
            409,
            f"Impossible de supprimer : {in_use} ligne(s) de production sont rattachées à ce bloc.",
        )
    has_wells = (await session.execute(
        select(func.count()).select_from(Well).where(Well.block_id == block_id)
    )).scalar_one()
    if has_wells > 0:
        raise HTTPException(
            409,
            f"Impossible de supprimer : {has_wells} puits sont rattachés à ce bloc.",
        )
    await session.delete(block)


@router.get("/wells", response_model=list[WellResponse])
async def list_wells(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    block: str | None = None,
) -> list[WellResponse]:
    stmt = select(Well).order_by(Well.code)
    if block is not None:
        stmt = stmt.join(Block).where(Block.code == block)
    rows = list((await session.execute(stmt)).scalars())
    return [
        WellResponse(id=w.id, code=w.code, block_id=w.block_id,
                     pump_type=w.pump_type, is_active=w.is_active)
        for w in rows
    ]


@router.post("/wells", response_model=WellResponse, status_code=201)
async def create_well(
    body: WellCreate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WellResponse:
    block = await session.get(Block, body.block_id)
    if block is None:
        raise HTTPException(404, "Bloc parent introuvable.")
    existing = (await session.execute(
        select(Well).where(Well.code == body.code)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, f"Le puits '{body.code}' existe déjà.")
    well = Well(
        code=body.code, block_id=body.block_id,
        pump_type=body.pump_type, is_active=body.is_active,
    )
    session.add(well)
    await session.flush()
    return WellResponse(id=well.id, code=well.code, block_id=well.block_id,
                        pump_type=well.pump_type, is_active=well.is_active)


@router.patch("/wells/{well_id}", response_model=WellResponse)
async def update_well(
    well_id: UUID,
    body: WellUpdate,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WellResponse:
    well = await session.get(Well, well_id)
    if well is None:
        raise HTTPException(404, "Puits introuvable.")
    if body.block_id is not None:
        block = await session.get(Block, body.block_id)
        if block is None:
            raise HTTPException(404, "Bloc parent introuvable.")
        well.block_id = body.block_id
    if body.pump_type is not None:
        well.pump_type = body.pump_type
    if body.is_active is not None:
        well.is_active = body.is_active
    await session.flush()
    return WellResponse(id=well.id, code=well.code, block_id=well.block_id,
                        pump_type=well.pump_type, is_active=well.is_active)


@router.delete("/wells/{well_id}", status_code=204)
async def delete_well(
    well_id: UUID,
    _: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    well = await session.get(Well, well_id)
    if well is None:
        raise HTTPException(404, "Puits introuvable.")
    in_use = (await session.execute(
        select(func.count()).select_from(DailyProduction).where(
            DailyProduction.well_id == well_id
        )
    )).scalar_one()
    if in_use > 0:
        raise HTTPException(
            409,
            f"Impossible de supprimer : {in_use} ligne(s) de production référencent ce puits.",
        )
    await session.delete(well)


@router.get("/daily")
async def list_daily(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_: Date = Query(default=None, alias="from"),
    to: Date | None = None,
    block: str | None = None,
    page: int = 1,
    page_size: int = Query(default=100, le=1000),
) -> dict:
    stmt = select(DailyProduction, Block).join(Block, DailyProduction.block_id == Block.id)
    if from_ is not None:
        stmt = stmt.where(DailyProduction.date >= from_)
    if to is not None:
        stmt = stmt.where(DailyProduction.date <= to)
    if block is not None:
        stmt = stmt.where(Block.code == block)
    stmt = stmt.order_by(DailyProduction.date.desc())
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = (await session.execute(stmt)).all()
    items = [
        {
            "id": str(dp.id), "date": dp.date.isoformat(), "block": b.code,
            "wells_total": dp.wells_total, "wells_active": dp.wells_active,
            "oil_bbl": float(dp.oil_bbl), "water_bbl": float(dp.water_bbl),
            "watercut_pct": float(dp.watercut_pct),
            "wor": float(dp.wor) if dp.wor is not None else None,
        } for dp, b in rows
    ]
    return {"items": items, "page": page, "page_size": page_size}


@router.post("/daily", status_code=201)
async def create_daily(
    body: DailyProductionCreate,
    user: Annotated[CurrentUser, Depends(require_permission("production:write"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    block = (await session.execute(
        select(Block).where(Block.code == body.block_code)
    )).scalar_one_or_none()
    if block is None:
        raise HTTPException(404, f"Block '{body.block_code}' not found")

    well_id: UUID | None = None
    if body.well_code:
        well = (await session.execute(
            select(Well).where(Well.code == body.well_code)
        )).scalar_one_or_none()
        if well is None:
            raise HTTPException(404, f"Well '{body.well_code}' not found")
        well_id = well.id

    wor = body.water_bbl / body.oil_bbl if body.oil_bbl > 0 else None
    dp = DailyProduction(
        date=body.date, block_id=block.id, well_id=well_id,
        wells_total=body.wells_total, wells_active=body.wells_active,
        oil_bbl=body.oil_bbl, water_bbl=body.water_bbl,
        watercut_pct=body.watercut_pct, wor=wor,
        source="manual", created_by=UUID(user.id),
    )
    session.add(dp)
    await session.flush()
    cache: KpiCache | None = getattr(request.app.state, "kpi_cache", None)
    if cache is not None:
        await cache.invalidate()
    return {"id": str(dp.id)}


@router.get("/kpis", response_model=KpiResponse)
async def kpis(
    _: Annotated[CurrentUser, Depends(require_permission("production:read"))],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    period: str = "30d",
) -> KpiResponse:
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period)
    if days is None:
        raise HTTPException(400, "period must be 7d|30d|90d|1y")

    cache: KpiCache | None = getattr(request.app.state, "kpi_cache", None)
    if cache is not None:
        cached = await cache.get(period)
        if cached is not None:
            return KpiResponse(**cached)

    end = Date.today()
    start = end - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    cur_stmt = select(
        func.coalesce(func.sum(DailyProduction.oil_bbl), 0),
        func.coalesce(func.avg(DailyProduction.watercut_pct), 0),
        func.coalesce(func.avg(DailyProduction.wells_active), 0),
        func.count(),
    ).where(DailyProduction.date.between(start, end))
    cur_total, cur_wc, cur_wells, cur_count = (await session.execute(cur_stmt)).one()

    prev_stmt = select(func.coalesce(func.sum(DailyProduction.oil_bbl), 0)).where(
        DailyProduction.date.between(prev_start, start - timedelta(days=1))
    )
    prev_total = float((await session.execute(prev_stmt)).scalar_one() or 0)

    delta = None
    if prev_total > 0:
        delta = ((float(cur_total) - prev_total) / prev_total) * 100

    avg_day = float(cur_total) / cur_count if cur_count else 0
    response = KpiResponse(
        period=period, production_total_bbl=float(cur_total),
        production_avg_bbl_day=avg_day, watercut_avg_pct=float(cur_wc),
        active_wells_avg=float(cur_wells), delta_vs_previous_pct=delta,
    )
    if cache is not None:
        await cache.set(period, response.model_dump())
    return response


@router.get("/export")
async def export_data(
    _: Annotated[CurrentUser, Depends(require_permission("production:export"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    format: str = "csv",
    from_: Date | None = Query(default=None, alias="from"),
    to: Date | None = None,
) -> Response:
    if format != "csv":
        raise HTTPException(400, "Only csv supported in v1")
    stmt = select(DailyProduction, Block).join(Block, DailyProduction.block_id == Block.id)
    if from_:
        stmt = stmt.where(DailyProduction.date >= from_)
    if to:
        stmt = stmt.where(DailyProduction.date <= to)
    stmt = stmt.order_by(DailyProduction.date)
    rows = (await session.execute(stmt)).all()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "block", "wells_total", "wells_active",
                "oil_bbl", "water_bbl", "watercut_pct", "wor"])
    for dp, b in rows:
        w.writerow([
            dp.date.isoformat(), b.code, dp.wells_total, dp.wells_active,
            float(dp.oil_bbl), float(dp.water_bbl),
            float(dp.watercut_pct), float(dp.wor) if dp.wor else "",
        ])
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=production.csv"},
    )
