"""Model training pipelines (RF + XGBoost). Pure Python, no streamlit dependency."""
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
    r2_score,
)
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


@dataclass
class TrainResult:
    blob_path: Path
    metrics: dict[str, Any]
    hyperparameters: dict[str, Any]


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
            max_depth=params.get("max_depth", 6), random_state=42,
        )
    if algorithm == "xgboost":
        if not HAS_XGB:
            raise RuntimeError("xgboost not installed")
        cls = XGBClassifier if task == "classification" else XGBRegressor
        return cls(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            tree_method="hist", random_state=42,
        )
    raise ValueError(f"Unknown algorithm: {algorithm}")


def _evaluate(task: str, y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    if task == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        }
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def train_model(
    *,
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    task: str,
    algorithm: str,
    params: dict[str, Any],
    models_dir: Path,
) -> TrainResult:
    if task not in ("classification", "regression"):
        raise ValueError(f"task must be classification|regression (got {task})")

    X = df[feature_cols]
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
    )

    model = _build_estimator(algorithm, task, params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = _evaluate(task, y_test.to_numpy(), y_pred)

    models_dir.mkdir(parents=True, exist_ok=True)
    blob_path = models_dir / f"{uuid4()}.joblib"
    joblib.dump(model, blob_path)

    return TrainResult(
        blob_path=blob_path,
        metrics=metrics,
        hyperparameters={**params, "algorithm": algorithm, "task": task},
    )
