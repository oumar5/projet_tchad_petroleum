from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base configuration shared across all SmartBarrel services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str
    environment: Literal["dev", "staging", "production"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = Field(..., description="postgresql+asyncpg://...")
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

    jwt_public_key_path: str = "/etc/jwt/public.pem"
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "smartbarrel-auth"

    cors_origins: list[str] = Field(default_factory=list)


@lru_cache
def get_settings(cls: type[BaseServiceSettings]) -> BaseServiceSettings:
    return cls()
