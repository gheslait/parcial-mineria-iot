"""Repositorio de `Anomalia`."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.anomalia import Anomalia
from app.repositories.base import BaseRepository


class AnomaliaRepository(BaseRepository[Anomalia]):
    modelo = Anomalia

    def listar_filtrado(
        self,
        *,
        id_sensor: int | None = None,
        metodo: str | None = None,
        desde: datetime | None = None,
        limite: int = 1000,
    ) -> list[Anomalia]:
        stmt = select(Anomalia).order_by(Anomalia.detectado_en.desc()).limit(limite)
        if id_sensor:
            stmt = stmt.where(Anomalia.id_sensor == id_sensor)
        if metodo:
            stmt = stmt.where(Anomalia.metodo == metodo)
        if desde:
            stmt = stmt.where(Anomalia.detectado_en >= desde)
        return list(self.db.scalars(stmt))
