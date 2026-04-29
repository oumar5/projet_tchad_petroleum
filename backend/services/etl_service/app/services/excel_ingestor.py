"""Excel ingestion logic — maps the legacy v2 Excel into PostgreSQL."""
import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PRODUCTION_SHEET = "Prod YOM BlocsFaillés X, Y et Z"
FAILURES_SHEET = "Historiq Pannes pompes"

PROD_COLUMNS = [
    "Date", "Nombre total des puits", "Nombre des puits actifs",
    "Production journaliere d'huile bbl", "Production journaliere d'eau bbl",
    "Teneur en eau (Watercut)", "Water Oil Ratio",
    "Production journaliere d'eau en kilo baril jour",
]


@dataclass
class IngestionResult:
    rows_processed: int
    rows_skipped: int
    rows_failed: int
    file_hash: str


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_production_sheet(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        file_path, sheet_name=PRODUCTION_SHEET,
        skiprows=4, header=None, names=PROD_COLUMNS,
    )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    return df


def read_failures_sheet(file_path: Path) -> pd.DataFrame:
    return pd.read_excel(file_path, sheet_name=FAILURES_SHEET)


async def ingest_excel(
    session: AsyncSession, file_path: Path, default_block: str = "X",
    strict_validation: bool = False,
) -> IngestionResult:
    """Idempotent ingestion: ON CONFLICT (date, block_id, well_id) DO NOTHING.

    If `strict_validation` is True, abort when Great Expectations fails.
    """
    from .data_quality import validate_production_df

    digest = file_sha256(file_path)
    df_prod = read_production_sheet(file_path)

    try:
        validation = validate_production_df(df_prod)
    except Exception:
        if strict_validation:
            raise
        validation = None
    if strict_validation and validation is not None and not validation.success:
        raise ValueError(
            f"Data validation failed: {validation.failed_expectations}"
        )

    # Ensure the default zone TCHAD exists (created by migration 0002_add_zones,
    # but kept idempotent here in case the ETL runs against an older DB).
    await session.execute(text("""
        INSERT INTO production.zones (code, name)
        VALUES ('TCHAD', 'Tchad — zone par défaut')
        ON CONFLICT (code) DO NOTHING
    """))
    zone_row = (await session.execute(text(
        "SELECT id FROM production.zones WHERE code = 'TCHAD'"
    ))).first()
    default_zone_id = zone_row[0]

    # Ensure default block exists, attached to the default zone.
    await session.execute(text("""
        INSERT INTO production.blocks (code, name, zone_id)
        VALUES (:code, :name, :zone_id)
        ON CONFLICT (code) DO NOTHING
    """), {
        "code": default_block,
        "name": f"Block {default_block}",
        "zone_id": default_zone_id,
    })

    block_row = (await session.execute(text(
        "SELECT id FROM production.blocks WHERE code = :code"
    ), {"code": default_block})).first()
    block_id = block_row[0]

    rows_processed = 0
    rows_skipped = 0
    rows_failed = 0

    for _, row in df_prod.iterrows():
        try:
            wells_total = int(row["Nombre total des puits"]) if pd.notna(row["Nombre total des puits"]) else 0
            wells_active = int(row["Nombre des puits actifs"]) if pd.notna(row["Nombre des puits actifs"]) else 0
            oil = max(float(row["Production journaliere d'huile bbl"] or 0), 0.0)
            water = max(float(row["Production journaliere d'eau bbl"] or 0), 0.0)
            wc = float(row["Teneur en eau (Watercut)"] or 0)
            # Excel parfois stocke watercut en fraction (0-1) au lieu de %
            if 0 < wc <= 1:
                wc = wc * 100
            wc = min(max(wc, 0.0), 100.0)
            wor = water / oil if oil > 0 else None

            sp = await session.begin_nested()
            try:
                result = await session.execute(text("""
                    INSERT INTO production.daily_production
                        (date, block_id, wells_total, wells_active,
                         oil_bbl, water_bbl, watercut_pct, wor, source)
                    VALUES (:date, :block_id, :wt, :wa, :oil, :water, :wc, :wor, 'excel_import')
                    ON CONFLICT (date, block_id, well_id) DO NOTHING
                """), {
                    "date": row["Date"].date(), "block_id": block_id,
                    "wt": wells_total, "wa": wells_active,
                    "oil": oil, "water": water, "wc": wc, "wor": wor,
                })
                await sp.commit()
            except Exception:
                await sp.rollback()
                raise

            if result.rowcount == 0:
                rows_skipped += 1
            else:
                rows_processed += 1
        except Exception:
            rows_failed += 1

    return IngestionResult(
        rows_processed=rows_processed,
        rows_skipped=rows_skipped,
        rows_failed=rows_failed,
        file_hash=digest,
    )
