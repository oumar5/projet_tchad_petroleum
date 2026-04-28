"""Synchronous training pipeline (RF + GBM + XGBoost).

This module is *the* ML training pipeline of v3 — equivalent of the Streamlit
``ClassicalModels`` family with the same feature engineering. It's called from
the Celery worker (``workers.celery_app.train_task``).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from .data_loader import load_production_df
from .feature_engineering import (
    prepare_forecast_features,
    prepare_maintenance_features,
    prepare_water_features,
)


# ----------------------------------------------------------------------------
# Public dataclass
# ----------------------------------------------------------------------------

@dataclass
class TrainResult:
    blob_path: Path
    metrics: dict[str, Any]
    hyperparameters: dict[str, Any]
    feature_cols: list[str]
    target_col: str
    n_train: int
    n_test: int


# ----------------------------------------------------------------------------
# Generic training helpers
# ----------------------------------------------------------------------------

def _build_estimator(algorithm: str, task: str, params: dict[str, Any]):
    if algorithm == "random_forest":
        cls = RandomForestClassifier if task == "classification" else RandomForestRegressor
        return cls(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 10),
            random_state=42, n_jobs=-1,
        )
    if algorithm == "gradient_boosting":
        cls = GradientBoostingClassifier if task == "classification" else GradientBoostingRegressor
        return cls(
            n_estimators=params.get("n_estimators", 100),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 6),
            random_state=42,
        )
    if algorithm == "xgboost":
        if not HAS_XGB:
            raise RuntimeError("xgboost not installed")
        cls = XGBClassifier if task == "classification" else XGBRegressor
        return cls(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            tree_method="hist",
            random_state=42,
        )
    raise ValueError(f"Unknown algorithm: {algorithm}")


def _evaluate(task: str, y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    if task == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        }
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _fit_and_persist(
    *,
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    task: str,
    algorithm: str,
    params: dict[str, Any],
    models_dir: Path,
    shuffle: bool = True,
) -> TrainResult:
    # Drop rows where any feature or target is NaN (lag/rolling features
    # leave a few NaN at the head of the dataframe).
    df = df.dropna(subset=[*feature_cols, target_col]).reset_index(drop=True)
    if len(df) < 30:
        raise ValueError(
            f"Données insuffisantes après dropna: {len(df)} (min 30)."
        )

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=shuffle,
    )

    model = _build_estimator(algorithm, task, params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = _evaluate(task, y_test.to_numpy(), y_pred)

    models_dir.mkdir(parents=True, exist_ok=True)
    blob_id = uuid4()
    blob_path = models_dir / f"{blob_id}.joblib"
    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
            "target_col": target_col,
            "task": task,
            "algorithm": algorithm,
        },
        blob_path,
    )

    return TrainResult(
        blob_path=blob_path,
        metrics=metrics,
        hyperparameters={**params, "algorithm": algorithm, "task": task},
        feature_cols=feature_cols,
        target_col=target_col,
        n_train=len(X_train),
        n_test=len(X_test),
    )


# ----------------------------------------------------------------------------
# Public entry point — model_type → real training
# ----------------------------------------------------------------------------

def train_for_type(
    *,
    model_type: str,
    algorithm: str,
    params: dict[str, Any],
    database_url: str,
    models_dir: Path,
) -> TrainResult:
    """Run the full pipeline for one of the 3 SmartBarrel model types.

    model_type ∈ {maintenance, forecast, water}.
    """
    prod = load_production_df(database_url)

    if model_type == "maintenance":
        df, feat, target = prepare_maintenance_features(prod, failures_df=None)
        task = "classification"
        # chronologically-ordered data: shuffle ok for classification
        return _fit_and_persist(
            df=df, feature_cols=feat, target_col=target,
            task=task, algorithm=algorithm, params=params,
            models_dir=models_dir, shuffle=True,
        )

    if model_type == "forecast":
        df, feat, target = prepare_forecast_features(prod)
        task = "regression"
        # time-series: no shuffle (preserve temporal order)
        return _fit_and_persist(
            df=df, feature_cols=feat, target_col=target,
            task=task, algorithm=algorithm, params=params,
            models_dir=models_dir, shuffle=False,
        )

    if model_type == "water":
        df, feat, target = prepare_water_features(prod)
        task = "regression"
        return _fit_and_persist(
            df=df, feature_cols=feat, target_col=target,
            task=task, algorithm=algorithm, params=params,
            models_dir=models_dir, shuffle=True,
        )

    raise ValueError(
        f"Unknown model_type '{model_type}'. Expected one of: maintenance, forecast, water."
    )
