from shared.config import BaseServiceSettings


class EtlSettings(BaseServiceSettings):
    service_name: str = "etl-service"
    upload_dir: str = "/tmp/etl_uploads"
    storage_backend: str = "local"
    s3_bucket: str = "smartbarrel-imports"
    s3_endpoint_url: str | None = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"


_settings: EtlSettings | None = None


def get_settings() -> EtlSettings:
    global _settings
    if _settings is None:
        _settings = EtlSettings()
    return _settings
