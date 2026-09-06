"""
Tabla 7 — `evento_riesgo`: alerta de riesgo de combustión detectada.

Guarda el `nivel`, el `score` compuesto (0–100) y los valores que lo dispararon.
La referencia a `lectura` es lógica (`id_lectura` + `lectura_medido_en`) sin FK
física, porque `lectura` es una hypertable de TimescaleDB.
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
    from app.models.regla_riesgo import ReglaRiesgo

ESTADOS_EVENTO = ("abierto", "reconocido", "cerrado")


class EventoRiesgo(Base):
    __tablename__ = "evento_riesgo"
    __table_args__ = (
        CheckConstraint(
            "nivel in ('bajo','medio','alto','critico')", name="evento_nivel_check"
        ),
        CheckConstraint(
            "estado in ('abierto','reconocido','cerrado')", name="evento_estado_check"
        ),
        CheckConstraint("score >= 0 and score <= 100", name="evento_score_check"),
        Index("ix_evento_dispositivo_tiempo", "id_dispositivo", "detectado_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    id_dispositivo: Mapped[int] = mapped_column(
        ForeignKey("dispositivo.id", name="evento_riesgo_id_dispositivo_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    id_regla: Mapped[int | None] = mapped_column(
        ForeignKey("regla_riesgo.id", name="evento_riesgo_id_regla_fkey", ondelete="SET NULL")
    )
    id_lectura: Mapped[int | None] = mapped_column(BigInteger)          # ref. lógica a lectura
    lectura_medido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    nivel: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    valor_mq7: Mapped[float | None] = mapped_column(Numeric(12, 4))
    valor_humedad: Mapped[float | None] = mapped_column(Numeric(12, 4))
    mensaje: Mapped[str] = mapped_column(String(300), nullable=False)
    estado: Mapped[str] = mapped_column(String(12), default="abierto", nullable=False)
    detectado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="eventos_riesgo")
    regla: Mapped["ReglaRiesgo | None"] = relationship(back_populates="eventos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EventoRiesgo {self.nivel} score={self.score} disp={self.id_dispositivo}>"
