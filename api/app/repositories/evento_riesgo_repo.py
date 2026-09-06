"""Repositorio de `EventoRiesgo`."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.evento_riesgo import EventoRiesgo
from app.repositories.base import BaseRepository


class EventoRiesgoRepository(BaseRepository[EventoRiesgo]):
    modelo = EventoRiesgo

    def listar_filtrado(
        self,
        *,
        id_dispositivo: int | None = None,
        nivel: str | None = None,
        estado: str | None = None,
        desde: datetime | None = None,
        limite: int = 500,
    ) -> list[EventoRiesgo]:
        stmt = select(EventoRiesgo).order_by(EventoRiesgo.detectado_en.desc()).limit(limite)
        if id_dispositivo:
            stmt = stmt.where(EventoRiesgo.id_dispositivo == id_dispositivo)
        if nivel:
            stmt = stmt.where(EventoRiesgo.nivel == nivel)
        if estado:
            stmt = stmt.where(EventoRiesgo.estado == estado)
        if desde:
            stmt = stmt.where(EventoRiesgo.detectado_en >= desde)
        return list(self.db.scalars(stmt))
