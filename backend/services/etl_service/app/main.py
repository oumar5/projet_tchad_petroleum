from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging
from shared.middleware import attach_cors
from shared.messaging import EventPublisher

from .api.routes_etl import router
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
    app.state.publisher = EventPublisher(settings.rabbitmq_url)
    try:
        await app.state.publisher.connect()
    except Exception:
        # Allow boot without RabbitMQ in degraded mode
        app.state.publisher = None
    yield
    if getattr(app.state, "publisher", None):
        await app.state.publisher.close()
    await engine.dispose()


app = FastAPI(
    title="SmartBarrel — etl-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/etl/openapi.json",
    docs_url="/v1/etl/docs",
)



attach_cors(app)
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "etl-service"}


app.include_router(router)
