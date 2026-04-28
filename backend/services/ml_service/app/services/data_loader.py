"""Read production data from PostgreSQL into the legacy pandas shape."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text

from .feature_engineering import (
    COL_DATE,
    COL_OIL,
    COL_WATER,
    COL_WC,
    COL_WELLS_ACTIVE,
    COL_WELLS_TOTAL,
)


def _sync_db_url(async_url: str) -> str:
    """Convert a SQLAlchemy async URL to a sync one (for joblib-friendly code)."""
    return async_url.replace("+asyncpg", "+psycopg2")


def load_production_df(database_url: str, *, block_code: str | None = None) -> pd.DataFrame:
    """Load all rows from production.daily_production as a pandas DataFrame
    with the legacy column names expected by the feature-engineering code.
    """
    engine = create_engine(_sync_db_url(database_url))
    where = ""
    params: dict = {}
    if block_code is not None:
        where = "WHERE b.code = :block"
        params["block"] = block_code

    sql = text(f"""
        SELECT
            d.date          AS "{COL_DATE}",
            d.oil_bbl       AS "{COL_OIL}",
            d.water_bbl     AS "{COL_WATER}",
            d.watercut_pct  AS "{COL_WC}",
            d.wells_active  AS "{COL_WELLS_ACTIVE}",
            d.wells_total   AS "{COL_WELLS_TOTAL}"
        FROM production.daily_production d
        JOIN production.blocks b ON b.id = d.block_id
        {where}
        ORDER BY d.date ASC
    """)

    with engine.begin() as conn:
        df = pd.read_sql(sql, conn, params=params)

    # Cast Decimal -> float so sklearn / numpy don't choke
    for col in (COL_OIL, COL_WATER, COL_WC):
        df[col] = df[col].astype(float)
    return df
