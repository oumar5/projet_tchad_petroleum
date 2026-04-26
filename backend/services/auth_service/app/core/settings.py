from pydantic import Field

from shared.config import BaseServiceSettings


class AuthSettings(BaseServiceSettings):
    service_name: str = "auth-service"

    jwt_private_key_path: str = "/etc/jwt/private.pem"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 60 * 60 * 24 * 7

    bcrypt_rounds: int = Field(default=12, ge=10, le=14)

    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@smartbarrel.td"


_settings: AuthSettings | None = None


def get_settings() -> AuthSettings:
    global _settings
    if _settings is None:
        _settings = AuthSettings()
    return _settings
