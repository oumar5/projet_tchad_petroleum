from shared.config import BaseServiceSettings


class MLSettings(BaseServiceSettings):
    service_name: str = "ml-service"
    models_dir: str = "/app/models"
    celery_broker_url: str = "amqp://guest:guest@rabbitmq:5672//"
    celery_result_backend: str = "redis://redis:6379/1"


_settings: MLSettings | None = None


def get_settings() -> MLSettings:
    global _settings
    if _settings is None:
        _settings = MLSettings()
    return _settings
