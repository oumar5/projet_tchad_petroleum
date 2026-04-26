from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging
from shared.middleware import attach_cors

from .api.routes_production import router
from .core.cache import KpiCache
from .core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level, service_name=settings.service_name)
    engine, factory = create_engine_and_session(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.jwt_validator = JWTValidator(
        public_key_path=settings.jwt_public_key_path,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer,
    )
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.kpi_cache = KpiCache(app.state.redis, ttl_seconds=settings.cache_ttl_seconds)
    yield
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="SmartBarrel — production-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/production/openapi.json",
    docs_url="/v1/production/docs",
)



attach_cors(app)
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "production-service"}


app.include_router(router)
