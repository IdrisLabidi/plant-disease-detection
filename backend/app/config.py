from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    env: str = "development"
    database_url: str = Field(..., alias="DATABASE_URL")
    secret_key: SecretStr = Field(..., alias="SECRET_KEY")
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    cors_origins: list[str] = []
    frontend_url: str = ""
    email_backend: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_from: str = "noreply@example.com"
    max_upload_mb: int = 8
    issuer: str = "plant-disease-api"
    audience: str = "plant-disease-app"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("email_backend")
    @classmethod
    def valid_email_backend(cls, value: str) -> str:
        if value not in {"console", "smtp"}:
            raise ValueError("EMAIL_BACKEND must be console or smtp")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
