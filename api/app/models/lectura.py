"""
Tabla 5 — `lectura`: log append-only de mediciones. **Hypertable de TimescaleDB**.

Particionada por `medido_en`; por eso la PK es compuesta `(id, medido_en)`
(TimescaleDB exige que la columna de partición forme parte de todo índice único).
Las FKs apuntan a tablas normales (`sensor`, `dispositivo`), lo cual TimescaleDB
sí permite. Nada apunta *hacia* esta hypertable con una FK física.
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
    from app.models.dispositivo import Dispositivo
    from app.models.sensor import Sensor

CALIDADES = ("valida", "sospechosa", "invalida")


class Lectura(Base):
    __tablename__ = "lectura"
    __table_args__ = (
        CheckConstraint(
            "calidad in ('valida','sospechosa','invalida')", name="lectura_calidad_check"
        ),
        Index("ix_lectura_sensor_tiempo", "id_sensor", "medido_en"),
        Index("ix_lectura_dispositivo_tiempo", "id_dispositivo", "medido_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    medido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, nullable=False
    )

    id_sensor: Mapped[int] = mapped_column(
        ForeignKey("sensor.id", name="lectura_id_sensor_fkey", ondelete="RESTRICT"),
        nullable=False,
    )
    id_dispositivo: Mapped[int] = mapped_column(
        ForeignKey("dispositivo.id", name="lectura_id_dispositivo_fkey", ondelete="RESTRICT"),
        nullable=False,
    )

    valor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unidad: Mapped[str] = mapped_column(String(15), nullable=False)
    crudo: Mapped[float | None] = mapped_column(Numeric(12, 4))  # lectura ADC sin convertir
    calidad: Mapped[str] = mapped_column(String(12), default="valida", nullable=False)
    recibido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sensor: Mapped["Sensor"] = relationship(back_populates="lecturas")
    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="lecturas")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Lectura s{self.id_sensor} {self.valor}{self.unidad} @{self.medido_en:%Y-%m-%d %H:%M}>"
