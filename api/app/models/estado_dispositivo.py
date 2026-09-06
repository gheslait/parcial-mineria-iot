"""
Tabla 9 — `estado_dispositivo`: telemetría de salud del ESP32 (heartbeat).

Registra RSSI de WiFi, memoria libre, uptime, si el último envío a la API fue
correcto y el texto mostrado en la LCD. Útil también como fuente para Power BI.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dispositivo import Dispositivo


class EstadoDispositivo(Base):
    __tablename__ = "estado_dispositivo"
    __table_args__ = (
        Index("ix_estado_disp_dispositivo_tiempo", "id_dispositivo", "reportado_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    id_dispositivo: Mapped[int] = mapped_column(
        ForeignKey(
            "dispositivo.id", name="estado_dispositivo_id_dispositivo_fkey", ondelete="CASCADE"
        ),
        nullable=False,
    )
    wifi_rssi: Mapped[int | None] = mapped_column()
    memoria_libre: Mapped[int | None] = mapped_column()
    uptime_seg: Mapped[int | None] = mapped_column(BigInteger)
    envio_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mensaje_lcd: Mapped[str | None] = mapped_column(String(64))
    reportado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="estados")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EstadoDispositivo disp={self.id_dispositivo} ok={self.envio_ok}>"
