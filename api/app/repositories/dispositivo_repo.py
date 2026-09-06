"""Repositorio de `Dispositivo`."""
from __future__ import annotations

from sqlalchemy import select

from app.models.dispositivo import Dispositivo
from app.repositories.base import BaseRepository


class DispositivoRepository(BaseRepository[Dispositivo]):
    modelo = Dispositivo

    def obtener_por_codigo(self, codigo: str) -> Dispositivo | None:
        return self.db.scalar(select(Dispositivo).where(Dispositivo.codigo == codigo))
