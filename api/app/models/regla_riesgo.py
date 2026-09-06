"""
Tabla 6 — `regla_riesgo`: motor de reglas para clasificar el riesgo de combustión.

Cada regla evalúa una magnitud contra un umbral y, si se cumple, aporta un
`nivel` (bajo/medio/alto/critico). El `EvaluadorRiesgo` (services/riesgo) las
combina para producir el `evento_riesgo`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import PkEnteraMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.evento_riesgo import EventoRiesgo
    from app.models.tipo_sensor import TipoSensor

OPERADORES = ("gt", "ge", "lt", "le", "between")
NIVELES = ("bajo", "medio", "alto", "critico")


class ReglaRiesgo(Base, PkEnteraMixin, TimestampMixin):
    __tablename__ = "regla_riesgo"
    __table_args__ = (
        UniqueConstraint("nombre", name="regla_riesgo_nombre_key"),
        CheckConstraint(
            "operador in ('gt','ge','lt','le','between')", name="regla_operador_check"
        ),
        CheckConstraint(
            "nivel in ('bajo','medio','alto','critico')", name="regla_nivel_check"
        ),
    )

    # NULL => regla compuesta (usa varias magnitudes, la resuelve el evaluador)
    id_tipo_sensor: Mapped[int | None] = mapped_column(
        ForeignKey("tipo_sensor.id", name="regla_riesgo_id_tipo_sensor_fkey", ondelete="CASCADE")
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    operador: Mapped[str] = mapped_column(String(10), nullable=False)
    umbral_min: Mapped[float | None] = mapped_column(Numeric(12, 4))
    umbral_max: Mapped[float | None] = mapped_column(Numeric(12, 4))
    nivel: Mapped[str] = mapped_column(String(10), nullable=False)
    puntaje: Mapped[int] = mapped_column(default=25, nullable=False)  # aporte al score 0-100
    mensaje: Mapped[str] = mapped_column(String(200), nullable=False)
    prioridad: Mapped[int] = mapped_column(default=100, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tipo_sensor: Mapped["TipoSensor | None"] = relationship(back_populates="reglas")
    eventos: Mapped[list["EventoRiesgo"]] = relationship(back_populates="regla")

    def evaluar(self, valor: float) -> bool:
        """Aplica el operador de la regla a un valor escalar."""
        umin, umax = self.umbral_min, self.umbral_max
        match self.operador:
            case "gt":
                return umin is not None and valor > float(umin)
            case "ge":
                return umin is not None and valor >= float(umin)
            case "lt":
                return umin is not None and valor < float(umin)
            case "le":
                return umin is not None and valor <= float(umin)
            case "between":
                return (
                    umin is not None
                    and umax is not None
                    and float(umin) <= valor <= float(umax)
                )
        return False

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ReglaRiesgo {self.nombre!r} -> {self.nivel}>"
