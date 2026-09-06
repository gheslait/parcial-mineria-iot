"""Esquemas base de los que heredan los demás (herencia de configuración)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EsquemaBase(BaseModel):
    """Config común: prohíbe campos extra en entrada, recorta strings."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EsquemaORM(BaseModel):
    """Para respuestas construidas desde objetos ORM (`from_attributes`)."""

    model_config = ConfigDict(from_attributes=True)
