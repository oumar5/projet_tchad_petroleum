from shared.config import BaseServiceSettings


class ProductionSettings(BaseServiceSettings):
    service_name: str = "production-service"
    cache_ttl_seconds: int = 300


_settings: ProductionSettings | None = None


def get_settings() -> ProductionSettings:
    global _settings
    if _settings is None:
        _settings = ProductionSettings()
    return _settings
