"""Repositorio de `Grupo`."""
from __future__ import annotations

from sqlalchemy import select

from app.models.grupo import Grupo
from app.repositories.base import BaseRepository


class GrupoRepository(BaseRepository[Grupo]):
    modelo = Grupo

    def obtener_por_numero(self, numero: int) -> Grupo | None:
        return self.db.scalar(select(Grupo).where(Grupo.numero == numero))
