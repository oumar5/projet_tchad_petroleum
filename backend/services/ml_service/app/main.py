from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging
from shared.messaging import EventPublisher

from .api.routes_ml import router
from .core.settings import get_settings
from .services.inference import InferenceService


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
    app.state.inference = InferenceService(settings.models_dir)
    app.state.publisher = EventPublisher(settings.rabbitmq_url)
    try:
        await app.state.publisher.connect()
    except Exception:
        app.state.publisher = None
    yield
    if getattr(app.state, "publisher", None):
        await app.state.publisher.close()
    await engine.dispose()


app = FastAPI(
    title="SmartBarrel — ml-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/ml/openapi.json",
    docs_url="/v1/ml/docs",
)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "ml-service"}


app.include_router(router)
