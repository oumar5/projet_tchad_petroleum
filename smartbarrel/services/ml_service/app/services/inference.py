"""Synchronous model inference. Loads pickled models from disk."""
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MLModel


class InferenceError(Exception):
    pass


class InferenceService:
    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self._cache: dict[UUID, Any] = {}

    async def get_active_model(self, session: AsyncSession, model_type: str) -> MLModel:
        stmt = select(MLModel).where(
            MLModel.model_type == model_type, MLModel.is_active == True  # noqa: E712
        )
        m = (await session.execute(stmt)).scalar_one_or_none()
        if m is None:
            raise InferenceError(f"No active model for type '{model_type}'")
        return m

    async def get_model_by_id(self, session: AsyncSession, model_id: UUID) -> MLModel:
        m = await session.get(MLModel, model_id)
        if m is None:
            raise InferenceError(f"Model {model_id} not found")
        return m

    def load(self, model_record: MLModel) -> Any:
        if model_record.id in self._cache:
            return self._cache[model_record.id]
        path = self.models_dir / f"{model_record.id}.joblib"
        if not path.exists():
            raise InferenceError(f"Model blob not found: {path}")
        loaded = joblib.load(path)
        self._cache[model_record.id] = loaded
        return loaded

    def predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        return model.predict(X)
