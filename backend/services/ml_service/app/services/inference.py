"""Synchronous model inference. Loads pickled models from disk."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MLModel
from .data_loader import load_production_df
from .feature_engineering import (
    COL_DATE,
    COL_OIL,
    COL_WATER,
    prepare_forecast_features,
    prepare_maintenance_features,
    prepare_water_features,
)


class InferenceError(Exception):
    pass


class InferenceService:
    """Loads .joblib bundles produced by training.train_for_type()."""

    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self._cache: dict[UUID, dict[str, Any]] = {}

    # ---- DB helpers ----

    async def get_active_model(self, session: AsyncSession, model_type: str) -> MLModel:
        stmt = select(MLModel).where(
            MLModel.model_type == model_type, MLModel.is_active == True  # noqa: E712
        )
        m = (await session.execute(stmt)).scalar_one_or_none()
        if m is None:
            raise InferenceError(
                f"Aucun modèle actif pour le type '{model_type}'. "
                "Lance un entraînement via POST /v1/ml/train."
            )
        return m

    async def get_model_by_id(self, session: AsyncSession, model_id: UUID) -> MLModel:
        m = await session.get(MLModel, model_id)
        if m is None:
            raise InferenceError(f"Model {model_id} not found")
        return m

    # ---- Bundle loading ----

    def _load_bundle(self, model_record: MLModel) -> dict[str, Any]:
        if model_record.id in self._cache:
            return self._cache[model_record.id]
        path = Path(model_record.blob_url)
        if not path.is_absolute():
            path = self.models_dir / path
        if not path.exists():
            raise InferenceError(f"Model blob introuvable: {path}")
        bundle = joblib.load(path)
        if not isinstance(bundle, dict):
            bundle = {"model": bundle, "feature_cols": None, "target_col": None}
        self._cache[model_record.id] = bundle
        return bundle

    # ---- High-level prediction APIs (one per model_type) ----

    def predict_maintenance(
        self,
        model_record: MLModel,
        database_url: str,
        *,
        block: str | None = None,
        horizon_days: int = 7,
    ) -> dict[str, Any]:
        bundle = self._load_bundle(model_record)
        prod = load_production_df(database_url, block_code=block)
        df, feature_cols, _ = prepare_maintenance_features(
            prod, failures_df=None, horizon_days=horizon_days,
        )
        X = df[feature_cols].dropna().tail(30)
        if X.empty:
            raise InferenceError("Pas assez de données récentes pour la prédiction.")

        model = bundle["model"]
        y_pred = model.predict(X)
        proba = None
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(X)[:, 1]
            except Exception:
                proba = None

        if proba is not None:
            risk = float(np.max(proba))
            mean_risk = float(np.mean(proba))
        else:
            risk = float(np.max(y_pred))
            mean_risk = float(np.mean(y_pred))

        last_date = df[COL_DATE].iloc[-1]
        if hasattr(last_date, "date"):
            last_date = last_date.date()

        if risk >= 0.6:
            level = "high"
        elif risk >= 0.3:
            level = "medium"
        else:
            level = "low"

        return {
            "predictions": [
                {
                    "block": block or "ALL",
                    "horizon_days": horizon_days,
                    "max_failure_risk": round(risk, 4),
                    "avg_failure_risk_30d": round(mean_risk, 4),
                    "risk_level": level,
                    "as_of": last_date.isoformat(),
                }
            ],
            "confidence": round(1.0 - mean_risk, 4),
        }

    def predict_forecast(
        self,
        model_record: MLModel,
        database_url: str,
        *,
        horizon_days: int = 30,
    ) -> dict[str, Any]:
        bundle = self._load_bundle(model_record)
        prod = load_production_df(database_url)
        df, feature_cols, target_col = prepare_forecast_features(prod)
        df = df.dropna(subset=[*feature_cols, target_col]).reset_index(drop=True)
        if df.empty:
            raise InferenceError("Pas de features disponibles pour la prévision.")

        model = bundle["model"]
        history = df.copy()
        last_row = history.iloc[-1].copy()
        last_date = last_row[COL_DATE]
        if not isinstance(last_date, pd.Timestamp):
            last_date = pd.Timestamp(last_date)

        ma14 = float(history[target_col].tail(14).mean())
        std14 = float(history[target_col].tail(14).std() or 0.0)

        forecast = []
        for step in range(1, horizon_days + 1):
            cur_date = last_date + pd.Timedelta(days=step)
            feat_row = last_row.copy()
            feat_row[COL_DATE] = cur_date
            feat_row["Year"] = cur_date.year
            feat_row["Month"] = cur_date.month
            feat_row["Day"] = cur_date.day
            feat_row["DayOfWeek"] = cur_date.dayofweek
            feat_row["DayOfYear"] = cur_date.dayofyear
            feat_row["Month_sin"] = np.sin(2 * np.pi * cur_date.month / 12)
            feat_row["Month_cos"] = np.cos(2 * np.pi * cur_date.month / 12)
            feat_row["DoW_sin"] = np.sin(2 * np.pi * cur_date.dayofweek / 7)
            feat_row["DoW_cos"] = np.cos(2 * np.pi * cur_date.dayofweek / 7)

            X_step = pd.DataFrame([feat_row[feature_cols].to_dict()])
            y_hat = float(model.predict(X_step)[0])
            forecast.append({
                "date": cur_date.date().isoformat(),
                "predicted_oil_bbl": round(y_hat, 2),
                "lower_bound_bbl": round(max(0.0, y_hat - 1.96 * std14), 2),
                "upper_bound_bbl": round(y_hat + 1.96 * std14, 2),
            })

            # Update lag features for the next iteration
            shift = {
                f"{target_col}_lag_1": y_hat,
                f"{target_col}_lag_7": history[target_col].iloc[-7] if len(history) >= 7 else y_hat,
                f"{target_col}_lag_14": history[target_col].iloc[-14] if len(history) >= 14 else y_hat,
            }
            for k, v in shift.items():
                if k in feat_row.index:
                    feat_row[k] = v
            new_row = feat_row.copy()
            new_row[target_col] = y_hat
            history = pd.concat(
                [history, pd.DataFrame([new_row])], ignore_index=True,
            )
            last_row = history.iloc[-1].copy()

        confidence = max(0.0, min(1.0, 1.0 - (std14 / max(ma14, 1.0))))
        return {
            "predictions": forecast,
            "confidence": round(confidence, 4),
        }

    def predict_water(
        self,
        model_record: MLModel,
        database_url: str,
        *,
        block: str | None = None,
        target_oil_bbl: float | None = None,
    ) -> dict[str, Any]:
        bundle = self._load_bundle(model_record)
        prod = load_production_df(database_url, block_code=block)
        df, feature_cols, _ = prepare_water_features(prod)
        if df.empty:
            raise InferenceError("Pas de features disponibles pour l'optimisation eau.")

        latest = df.iloc[[-1]].copy()
        model = bundle["model"]
        baseline_eff = float(model.predict(latest[feature_cols])[0])

        cur_water = float(latest[COL_WATER].iloc[0])
        cur_oil = float(latest[COL_OIL].iloc[0])

        candidates = []
        for factor in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
            row = latest.copy()
            new_water = max(0.0, cur_water * factor)
            row[COL_WATER] = new_water
            row["Water_Production_Ratio"] = new_water / (cur_oil + 1)
            row[f"{COL_WATER}_MA_7"] = (df[COL_WATER].tail(6).sum() + new_water) / 7
            eff = float(model.predict(row[feature_cols])[0])
            candidates.append({"injection_bbl": new_water, "efficiency": eff})

        best = max(candidates, key=lambda c: c["efficiency"])

        if target_oil_bbl is not None and best["efficiency"] > 0:
            expected_oil = max(cur_oil, target_oil_bbl)
        else:
            expected_oil = cur_oil * (1.0 + (best["efficiency"] - baseline_eff))

        sweep_pct = float(min(99.5, max(5.0, best["efficiency"] * 100)))

        return {
            "predictions": [
                {
                    "block": block or "ALL",
                    "current_injection_bbl": round(cur_water, 2),
                    "recommended_injection_bbl": round(best["injection_bbl"], 2),
                    "expected_oil_bbl": round(max(0.0, expected_oil), 2),
                    "sweep_efficiency_pct": round(sweep_pct, 2),
                    "baseline_efficiency": round(baseline_eff, 4),
                }
            ],
            "confidence": round(min(1.0, max(0.0, baseline_eff)), 4),
        }
