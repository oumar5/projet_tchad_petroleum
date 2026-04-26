from shared.config import BaseServiceSettings


class EtlSettings(BaseServiceSettings):
    service_name: str = "etl-service"
    upload_dir: str = "/app/data/uploads"


_settings: EtlSettings | None = None


def get_settings() -> EtlSettings:
    global _settings
    if _settings is None:
        _settings = EtlSettings()
    return _settings
