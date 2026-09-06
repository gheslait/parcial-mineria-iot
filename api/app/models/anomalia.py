"""
Tabla 8 — `anomalia`: valor atípico detectado en una lectura.

`metodo` indica qué detector la marcó (`zscore`, `iqr`, `rango_fisico`).
FK física a `sensor` (tabla normal); la referencia a `lectura` es lógica.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sensor import Sensor

METODOS = ("zscore", "iqr", "rango_fisico")


class Anomalia(Base):
    __tablename__ = "anomalia"
    __table_args__ = (
        CheckConstraint(
            "metodo in ('zscore','iqr','rango_fisico')", name="anomalia_metodo_check"
        ),
        Index("ix_anomalia_sensor_tiempo", "id_sensor", "detectado_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    id_sensor: Mapped[int] = mapped_column(
        ForeignKey("sensor.id", name="anomalia_id_sensor_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    id_lectura: Mapped[int | None] = mapped_column(BigInteger)          # ref. lógica a lectura
    lectura_medido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    metodo: Mapped[str] = mapped_column(String(15), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)  # z, distancia IQR, etc.
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sensor: Mapped["Sensor"] = relationship(back_populates="anomalias")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Anomalia {self.metodo} valor={self.valor} score={self.score}>"
