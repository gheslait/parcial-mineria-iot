"""
Tabla 3 — `tipo_sensor`: catálogo de tipos de sensor.

Es la fuente de verdad para la **validación de rango físico**: `rango_min` y
`rango_max` definen los valores admisibles para cada magnitud (p. ej. MQ7:
0–1000 ppm; humedad de suelo: 0–100 %).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import PkEnteraMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.regla_riesgo import ReglaRiesgo
    from app.models.sensor import Sensor


class TipoSensor(Base, PkEnteraMixin, TimestampMixin):
    __tablename__ = "tipo_sensor"

    clave: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # MQ7, HUM_SUELO
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    magnitud: Mapped[str] = mapped_column(String(80), nullable=False)
    unidad: Mapped[str] = mapped_column(String(15), nullable=False)
    rango_min: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    rango_max: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    precision: Mapped[float | None] = mapped_column(Numeric(8, 4))
    descripcion: Mapped[str | None] = mapped_column(String(300))

    sensores: Mapped[list["Sensor"]] = relationship(back_populates="tipo_sensor")
    reglas: Mapped[list["ReglaRiesgo"]] = relationship(back_populates="tipo_sensor")

    def contiene(self, valor: float) -> bool:
        """True si `valor` cae dentro del rango físico declarado del sensor."""
        return float(self.rango_min) <= valor <= float(self.rango_max)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TipoSensor {self.clave!r} [{self.rango_min}-{self.rango_max} {self.unidad}]>"
