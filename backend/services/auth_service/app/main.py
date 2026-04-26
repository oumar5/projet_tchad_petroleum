"""auth-service entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging
from shared.middleware import attach_cors

from .api.routes_admin import router as admin_router
from .api.routes_auth import router as auth_router
from .core.redis_client import init_redis
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
    init_redis(settings.redis_url)
    yield
    await engine.dispose()


app = FastAPI(
    title="SmartBarrel — auth-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/auth/openapi.json",
    docs_url="/v1/auth/docs",
)



attach_cors(app)
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "auth-service"}


app.include_router(auth_router)
app.include_router(admin_router)
