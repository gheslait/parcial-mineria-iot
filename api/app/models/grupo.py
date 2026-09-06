"""Tabla 1 — `grupo`: identificación del grupo del parcial."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import PkEnteraMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.dispositivo import Dispositivo


class Grupo(Base, PkEnteraMixin, TimestampMixin):
    __tablename__ = "grupo"
    __table_args__ = (UniqueConstraint("numero", name="grupo_numero_key"),)

    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    numero: Mapped[int] = mapped_column(nullable=False)
    curso: Mapped[str] = mapped_column(String(120), default="Mineria de Datos", nullable=False)

    dispositivos: Mapped[list["Dispositivo"]] = relationship(
        back_populates="grupo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Grupo #{self.numero} {self.nombre!r}>"
