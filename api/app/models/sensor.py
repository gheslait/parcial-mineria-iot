"""Tabla 4 — `sensor`: un sensor físico concreto montado en un dispositivo."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import PkEnteraMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.anomalia import Anomalia
    from app.models.dispositivo import Dispositivo
    from app.models.lectura import Lectura
    from app.models.tipo_sensor import TipoSensor


class Sensor(Base, PkEnteraMixin, TimestampMixin):
    __tablename__ = "sensor"
    __table_args__ = (
        UniqueConstraint("id_dispositivo", "id_tipo_sensor", name="sensor_disp_tipo_key"),
    )

    id_dispositivo: Mapped[int] = mapped_column(
        ForeignKey("dispositivo.id", name="sensor_id_dispositivo_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    id_tipo_sensor: Mapped[int] = mapped_column(
        ForeignKey("tipo_sensor.id", name="sensor_id_tipo_sensor_fkey", ondelete="RESTRICT"),
        nullable=False,
    )
    etiqueta: Mapped[str] = mapped_column(String(60), nullable=False)
    pin: Mapped[str | None] = mapped_column(String(10))
    fecha_instalacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_ultima_calibracion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="sensores")
    tipo_sensor: Mapped["TipoSensor"] = relationship(back_populates="sensores")
    lecturas: Mapped[list["Lectura"]] = relationship(back_populates="sensor")
    anomalias: Mapped[list["Anomalia"]] = relationship(back_populates="sensor")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Sensor {self.etiqueta!r} disp={self.id_dispositivo}>"
