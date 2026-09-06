"""Repositorio de `ReglaRiesgo`."""
from __future__ import annotations

from sqlalchemy import select

from app.models.regla_riesgo import ReglaRiesgo
from app.repositories.base import BaseRepository


class ReglaRiesgoRepository(BaseRepository[ReglaRiesgo]):
    modelo = ReglaRiesgo

    def activas(self) -> list[ReglaRiesgo]:
        stmt = (
            select(ReglaRiesgo)
            .where(ReglaRiesgo.activo.is_(True))
            .order_by(ReglaRiesgo.prioridad)
        )
        return list(self.db.scalars(stmt))
