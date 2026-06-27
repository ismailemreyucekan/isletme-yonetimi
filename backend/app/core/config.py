"""Uygulama ayarları — .env'den okunur (Pydantic Settings)."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Uygulama
    app_name: str = "Kasa"
    environment: str = "development"
    debug: bool = True

    # Veritabanı / Redis
    database_url: str = "postgresql+asyncpg://kasa:kasa@localhost:5432/kasa"
    redis_url: str = "redis://localhost:6379/0"

    # Güvenlik / JWT
    secret_key: str = "change-me-in-production-with-a-long-random-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # CORS — NoDecode: pydantic-settings ortam değişkenini JSON olarak çözmeye
    # çalışmasın; ham string'i alıp aşağıdaki validator virgülden böler.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        """CORS_ORIGINS hem virgüllü string hem liste olarak verilebilsin."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
