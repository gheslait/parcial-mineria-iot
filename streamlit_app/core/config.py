"""Configuración de la app (lee streamlit_app/.env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV, env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    db_schema: str = Field(default="combustion_riesgo", alias="DB_SCHEMA")

    @field_validator("database_url")
    @classmethod
    def _psycopg2(cls, v: str) -> str:
        return v.replace("postgresql://", "postgresql+psycopg2://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
