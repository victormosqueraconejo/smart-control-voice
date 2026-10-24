"""Validated runtime configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str
    telegram_allowed_ids: set[int] = Field(default_factory=set)
    groq_api_key: str
    groq_model: str = "llama3-8b-8192"
    kodi_url: str = "http://127.0.0.1:8080/jsonrpc"
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    audio_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    audio_max_duration_seconds: int = Field(default=120, gt=0)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    work_directory: str = "/tmp/smart-control-voice"
    source_caracol_url: str | None = None
    source_rcn_url: str | None = None
    source_telepacifico_url: str | None = None
    source_noticias_url: str | None = None
    source_peliculas_investigacion_url: str | None = None

    @field_validator("telegram_allowed_ids", mode="before")
    @classmethod
    def parse_allowed_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return {int(item.strip()) for item in value.split(",") if item.strip()}
        return value

    @field_validator("whisper_model")
    @classmethod
    def restrict_whisper_model(cls, value: str) -> str:
        if value not in {"tiny", "base"}:
            raise ValueError("whisper_model must be 'tiny' or 'base'")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]