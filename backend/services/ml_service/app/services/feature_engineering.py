"""Feature engineering ported from the Streamlit v2 pipeline.

Same column names as the Streamlit pipeline so that the training code can be
reused as-is. The data_loader is responsible for projecting the SQL columns of
production.daily_production into these legacy column names.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Legacy column names (kept identical to the Streamlit pipeline so that the
# feature-engineering math doesn't drift between systems).
COL_DATE = "Date"
COL_OIL = "Production journaliere d'huile bbl"
COL_WATER = "Production journaliere d'eau bbl"
COL_WC = "Teneur en eau (Watercut)"
COL_WELLS_ACTIVE = "Nombre des puits actifs"
COL_WELLS_TOTAL = "Nombre total des puits"


# ----------------------------------------------------------------------------
# Maintenance — classification (failure within next N days)
# ----------------------------------------------------------------------------

def prepare_maintenance_features(
    production_df: pd.DataFrame,
    failures_df: pd.DataFrame | None = None,
    *,
    horizon_days: int = 7,
) -> tuple[pd.DataFrame, list[str], str]:
    """Return (features_df, feature_cols, target_col).

    Mirrors :class:`MaintenancePredictiveModel.prepare_features` from the
    Streamlit pipeline (rolling means, std, trend, days-since-start) and
    tags rows with ``Failure_Next_Days``.
    """
    if production_df.empty:
        raise ValueError("Aucune donnée de production pour la maintenance.")

    df = production_df.copy()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE])
    df = df.sort_values(COL_DATE).reset_index(drop=True)

    n = len(df)
    window_7 = min(7, max(1, n // 4))
    window_30 = min(30, max(1, n // 2))

    df["Production_MA_7"] = df[COL_OIL].rolling(window=window_7, min_periods=1).mean()
    df["Production_MA_30"] = df[COL_OIL].rolling(window=window_30, min_periods=1).mean()
    df["Production_Std_7"] = df[COL_OIL].rolling(window=window_7, min_periods=1).std()
    df["Watercut_MA_7"] = df[COL_WC].rolling(window=window_7, min_periods=1).mean()
    df["Production_Trend"] = df[COL_OIL].diff().fillna(0)
    df["Days_Since_Start"] = (df[COL_DATE] - df[COL_DATE].min()).dt.days

    # Failure labels
    df["Failure_Next_Days"] = 0
    if failures_df is not None and not failures_df.empty and COL_DATE in failures_df.columns:
        f = failures_df.copy()
        f[COL_DATE] = pd.to_datetime(f[COL_DATE], errors="coerce")
        f = f.dropna(subset=[COL_DATE])
        failure_dates = set(f[COL_DATE].dt.date)
        for i, row in df.iterrows():
            cur = row[COL_DATE].date()
            for j in range(1, horizon_days + 1):
                future = cur + pd.Timedelta(days=j)
                if future.date() in failure_dates:
                    df.loc[i, "Failure_Next_Days"] = 1
                    break
    else:
        # Pas de table failures — créer un signal synthétique léger pour
        # éviter un dataset complètement déséquilibré (10 % de pannes).
        rng = np.random.default_rng(42)
        df["Failure_Next_Days"] = rng.choice([0, 1], size=n, p=[0.9, 0.1])

    df = df.fillna({
        "Production_MA_7": df[COL_OIL].median(),
        "Production_MA_30": df[COL_OIL].median(),
        "Production_Std_7": 0,
        "Watercut_MA_7": df[COL_WC].median(),
        "Production_Trend": 0,
    })
    df = df.dropna(subset=[COL_OIL, COL_WC])

    feature_cols = [
        COL_OIL,
        COL_WC,
        COL_WELLS_ACTIVE,
        "Production_MA_7",
        "Production_MA_30",
        "Production_Std_7",
        "Watercut_MA_7",
        "Production_Trend",
        "Days_Since_Start",
    ]
    return df, feature_cols, "Failure_Next_Days"


# ----------------------------------------------------------------------------
# Forecast — regression (oil production, time-series with lag features)
# ----------------------------------------------------------------------------

def prepare_forecast_features(
    production_df: pd.DataFrame,
    *,
    target_col: str = COL_OIL,
) -> tuple[pd.DataFrame, list[str], str]:
    """Lag/rolling features for time-series production forecasting."""
    if len(production_df) < 60:
        raise ValueError(
            f"Données insuffisantes pour les features temporelles: {len(production_df)} (min 60)."
        )

    df = production_df.copy()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE])
    df = df.sort_values(COL_DATE).reset_index(drop=True)

    # Temporal features
    df["Year"] = df[COL_DATE].dt.year
    df["Month"] = df[COL_DATE].dt.month
    df["Day"] = df[COL_DATE].dt.day
    df["DayOfWeek"] = df[COL_DATE].dt.dayofweek
    df["DayOfYear"] = df[COL_DATE].dt.dayofyear
    df["Month_sin"] = np.sin(2 * np.pi * df["Month"] / 12)
    df["Month_cos"] = np.cos(2 * np.pi * df["Month"] / 12)
    df["DoW_sin"] = np.sin(2 * np.pi * df["DayOfWeek"] / 7)
    df["DoW_cos"] = np.cos(2 * np.pi * df["DayOfWeek"] / 7)

    # Lag features
    for lag in (1, 7, 14):
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

    # Rolling features
    for window in (7, 14):
        df[f"{target_col}_ma_{window}"] = df[target_col].rolling(window).mean()
        df[f"{target_col}_std_{window}"] = df[target_col].rolling(window).std()

    # Trend features
    df["trend_diff_7"] = df[target_col].diff(7)
    df["trend_diff_30"] = df[target_col].diff(30)

    # Drop rows with too many NaN (created by the largest rolling/lag window)
    df = df.dropna(thresh=int(len(df.columns) * 0.6))

    if len(df) < 10:
        raise ValueError(
            f"Données insuffisantes après nettoyage: {len(df)} points (min 10)."
        )

    feature_cols = [
        COL_WELLS_ACTIVE,
        COL_WATER,
        COL_WC,
        "Year", "Month", "Day", "DayOfWeek", "DayOfYear",
        "Month_sin", "Month_cos", "DoW_sin", "DoW_cos",
        f"{target_col}_lag_1", f"{target_col}_lag_7", f"{target_col}_lag_14",
        f"{target_col}_ma_7", f"{target_col}_ma_14",
        f"{target_col}_std_7", f"{target_col}_std_14",
        "trend_diff_7", "trend_diff_30",
    ]
    return df, feature_cols, target_col


# ----------------------------------------------------------------------------
# Water injection — regression (oil/water efficiency proxy)
# ----------------------------------------------------------------------------

def prepare_water_features(
    production_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], str]:
    """Feature set for the water-injection optimisation regressor."""
    df = production_df.copy()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE])
    df = df.sort_values(COL_DATE).reset_index(drop=True)

    df["Oil_Water_Efficiency"] = df[COL_OIL] / (df[COL_WATER] + 1)
    df["Watercut_Change"] = df[COL_WC].diff()
    df["Production_Change"] = df[COL_OIL].diff()
    df["Water_Production_Ratio"] = df[COL_WATER] / (df[COL_OIL] + 1)

    for col in (COL_OIL, COL_WATER, COL_WC):
        df[f"{col}_MA_7"] = df[col].rolling(7).mean()
        df[f"{col}_MA_30"] = df[col].rolling(30).mean()

    df = df.dropna()

    if len(df) < 30:
        raise ValueError(
            f"Données insuffisantes pour l'optimisation injection: {len(df)} (min 30)."
        )

    feature_cols = [
        COL_OIL, COL_WATER, COL_WC, COL_WELLS_ACTIVE,
        "Watercut_Change", "Production_Change", "Water_Production_Ratio",
        f"{COL_OIL}_MA_7", f"{COL_OIL}_MA_30",
        f"{COL_WATER}_MA_7", f"{COL_WATER}_MA_30",
        f"{COL_WC}_MA_7", f"{COL_WC}_MA_30",
    ]
    return df, feature_cols, "Oil_Water_Efficiency"
