"""Redis client for refresh token blocklist."""
from redis.asyncio import Redis

_client: Redis | None = None


def init_redis(redis_url: str) -> Redis:
    global _client
    _client = Redis.from_url(redis_url, decode_responses=True)
    return _client


def get_redis() -> Redis:
    if _client is None:
        raise RuntimeError("Redis not initialized")
    return _client


async def blocklist_jti(jti: str, ttl_seconds: int) -> None:
    await get_redis().setex(f"jwt:blocklist:{jti}", ttl_seconds, "1")


async def is_jti_blocklisted(jti: str) -> bool:
    return bool(await get_redis().exists(f"jwt:blocklist:{jti}"))


async def record_login_failure(email: str) -> int:
    key = f"login:fail:{email.lower()}"
    count = await get_redis().incr(key)
    if count == 1:
        await get_redis().expire(key, 900)
    return int(count)


async def reset_login_failures(email: str) -> None:
    await get_redis().delete(f"login:fail:{email.lower()}")
