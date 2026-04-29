from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.auth import JWTValidator
from shared.db import create_engine_and_session
from shared.logging import configure_logging
from shared.messaging import EventPublisher
from shared.middleware import attach_cors
from shared.storage import build_storage

from .api.routes_maintenance import router
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
    app.state.storage_backend = settings.storage_backend
    app.state.storage = build_storage(
        backend=settings.storage_backend,
        local_dir=settings.attachments_dir,
        s3_bucket=settings.s3_bucket,
        s3_endpoint=settings.s3_endpoint_url,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
        s3_region=settings.s3_region,
    )
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
    title="SmartBarrel — maintenance-service",
    version="3.0.0",
    lifespan=lifespan,
    openapi_url="/v1/maintenance/openapi.json",
    docs_url="/v1/maintenance/docs",
)



attach_cors(app)
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "maintenance-service"}


app.include_router(router)
