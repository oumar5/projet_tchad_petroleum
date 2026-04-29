from shared.config import BaseServiceSettings


class MaintenanceSettings(BaseServiceSettings):
    service_name: str = "maintenance-service"
    attachments_dir: str = "/app/attachments"
    storage_backend: str = "local"  # 'local' or 's3'
    s3_bucket: str = "smartbarrel-attachments"
    s3_endpoint_url: str | None = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"


_settings: MaintenanceSettings | None = None


def get_settings() -> MaintenanceSettings:
    global _settings
    if _settings is None:
        _settings = MaintenanceSettings()
    return _settings
