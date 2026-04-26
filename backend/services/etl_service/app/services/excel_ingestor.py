"""Excel ingestion logic — maps the legacy v2 Excel into PostgreSQL."""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    session: AsyncSession, file_path: Path, default_block: str = "X"
) -> IngestionResult:
    """Idempotent ingestion: ON CONFLICT (date, block_id, well_id) DO NOTHING."""
    digest = file_sha256(file_path)
    df_prod = read_production_sheet(file_path)

    # Ensure default block exists
    await session.execute(text("""
        INSERT INTO production.blocks (code, name)
        VALUES (:code, :name)
        ON CONFLICT (code) DO NOTHING
    """), {"code": default_block, "name": f"Block {default_block}"})

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
            oil = float(row["Production journaliere d'huile bbl"] or 0)
            water = float(row["Production journaliere d'eau bbl"] or 0)
            wc = float(row["Teneur en eau (Watercut)"] or 0)
            if wc > 100:
                wc = 100
            wor = water / oil if oil > 0 else None

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
