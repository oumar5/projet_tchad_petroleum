from shared.config import BaseServiceSettings


class MaintenanceSettings(BaseServiceSettings):
    service_name: str = "maintenance-service"
    attachments_dir: str = "/app/attachments"


_settings: MaintenanceSettings | None = None


def get_settings() -> MaintenanceSettings:
    global _settings
    if _settings is None:
        _settings = MaintenanceSettings()
    return _settings
