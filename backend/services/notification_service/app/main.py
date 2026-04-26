import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging

from .api.routes_notifications import router
from .core.settings import get_settings
from .workers.event_consumer import run_consumer


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
    consumer_task = asyncio.create_task(run_consumer(settings, factory))
    app.state.consumer_task = consumer_task
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(
    title="SmartBarrel — notification-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/notifications/openapi.json",
    docs_url="/v1/notifications/docs",
)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "notification-service"}


app.include_router(router)
