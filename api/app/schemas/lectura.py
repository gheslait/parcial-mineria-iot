"""Esquemas de salida y de filtro para `lectura`."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.base import EsquemaBase, EsquemaORM


class LecturaOut(EsquemaORM):
    id: int
    medido_en: datetime
    id_sensor: int
    id_dispositivo: int
    valor: float
    unidad: str
    crudo: float | None
    calidad: str
    recibido_en: datetime


class FiltroLecturas(EsquemaBase):
    """Filtros dinámicos (los mismos que expone la app Streamlit)."""

    desde: datetime | None = None
    hasta: datetime | None = None
    tipo_sensor: str | None = Field(default=None, description="clave: MQ7 / HUM_SUELO")
    codigo_dispositivo: str | None = None
    valor_min: float | None = None
    valor_max: float | None = None
    calidad: str | None = None
    limite: int = Field(default=1000, ge=1, le=50000)

    @model_validator(mode="after")
    def _coherencia(self) -> "FiltroLecturas":
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError("'desde' no puede ser posterior a 'hasta'")
        if (
            self.valor_min is not None
            and self.valor_max is not None
            and self.valor_min > self.valor_max
        ):
            raise ValueError("'valor_min' no puede ser mayor que 'valor_max'")
        return self
