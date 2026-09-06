"""
Configuración de la aplicación.

`Settings` encapsula todas las variables de entorno en un único objeto tipado
(patrón *Singleton* vía `lru_cache`). Ninguna otra capa lee `os.environ`
directamente: siempre piden `get_settings()`.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Parámetros de ejecución leídos de `api/.env`."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(alias="DATABASE_URL")
    db_schema: str = Field(default="combustion_riesgo", alias="DB_SCHEMA")

    grupo_nombre: str = Field(default="Grupo Riesgo de Combustion", alias="GRUPO_NOMBRE")
    grupo_numero: int = Field(default=1, alias="GRUPO_NUMERO")
    dispositivo_codigo: str = Field(default="ESP32-COMB-01", alias="DISPOSITIVO_CODIGO")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("database_url")
    @classmethod
    def _exigir_driver_psycopg2(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL debe ser una cadena postgresql://…")
        # Normaliza a psycopg2 para que SQLAlchemy no intente psycopg (v3).
        return v.replace("postgresql://", "postgresql+psycopg2://", 1)

    @property
    def db_schema_seguro(self) -> str:
        """Nombre de schema validado (solo identificador simple)."""
        s = self.db_schema.strip()
        if not s.replace("_", "").isalnum():
            raise ValueError(f"DB_SCHEMA inválido: {s!r}")
        return s


@lru_cache
def get_settings() -> Settings:
    """Devuelve la única instancia de `Settings` del proceso."""
    return Settings()  # type: ignore[call-arg]
