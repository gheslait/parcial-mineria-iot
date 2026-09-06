"""Tabla 2 — `dispositivo`: el ESP32 físico que genera las mediciones."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import PkEnteraMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.estado_dispositivo import EstadoDispositivo
    from app.models.evento_riesgo import EventoRiesgo
    from app.models.grupo import Grupo
    from app.models.lectura import Lectura
    from app.models.sensor import Sensor


class Dispositivo(Base, PkEnteraMixin, TimestampMixin):
    __tablename__ = "dispositivo"

    id_grupo: Mapped[int] = mapped_column(
        ForeignKey("grupo.id", name="dispositivo_id_grupo_fkey", ondelete="RESTRICT"),
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    ubicacion: Mapped[str | None] = mapped_column(String(150))
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    mac_address: Mapped[str | None] = mapped_column(String(17), unique=True)
    firmware_version: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    grupo: Mapped["Grupo"] = relationship(back_populates="dispositivos")
    sensores: Mapped[list["Sensor"]] = relationship(
        back_populates="dispositivo", cascade="all, delete-orphan"
    )
    lecturas: Mapped[list["Lectura"]] = relationship(back_populates="dispositivo")
    eventos_riesgo: Mapped[list["EventoRiesgo"]] = relationship(back_populates="dispositivo")
    estados: Mapped[list["EstadoDispositivo"]] = relationship(back_populates="dispositivo")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dispositivo {self.codigo!r}>"
