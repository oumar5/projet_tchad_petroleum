from shared.config import BaseServiceSettings


class NotificationSettings(BaseServiceSettings):
    service_name: str = "notification-service"
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@smartbarrel.td"
    fcm_credentials_path: str | None = None


_settings: NotificationSettings | None = None


def get_settings() -> NotificationSettings:
    global _settings
    if _settings is None:
        _settings = NotificationSettings()
    return _settings
