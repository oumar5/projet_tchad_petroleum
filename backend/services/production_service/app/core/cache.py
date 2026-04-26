"""Redis-backed cache for KPIs."""
import json
from typing import Any

from redis.asyncio import Redis


class KpiCache:
    def __init__(self, redis: Redis, ttl_seconds: int = 300):
        self.redis = redis
        self.ttl = ttl_seconds

    @staticmethod
    def _key(period: str) -> str:
        return f"production:kpis:{period}"

    async def get(self, period: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key(period))
        return json.loads(raw) if raw else None

    async def set(self, period: str, payload: dict[str, Any]) -> None:
        await self.redis.setex(self._key(period), self.ttl, json.dumps(payload))

    async def invalidate(self) -> None:
        async for k in self.redis.scan_iter("production:kpis:*"):
            await self.redis.delete(k)
