"""Repositorio de `EstadoDispositivo`."""
from __future__ import annotations

from sqlalchemy import select

from app.models.estado_dispositivo import EstadoDispositivo
from app.repositories.base import BaseRepository


class EstadoDispositivoRepository(BaseRepository[EstadoDispositivo]):
    modelo = EstadoDispositivo

    def ultimos(self, id_dispositivo: int, n: int = 100) -> list[EstadoDispositivo]:
        stmt = (
            select(EstadoDispositivo)
            .where(EstadoDispositivo.id_dispositivo == id_dispositivo)
            .order_by(EstadoDispositivo.reportado_en.desc())
            .limit(n)
        )
        return list(self.db.scalars(stmt))
