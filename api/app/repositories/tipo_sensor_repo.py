"""Repositorio de `TipoSensor` (catálogo con caché en memoria por request)."""
from __future__ import annotations

from sqlalchemy import select

from app.models.tipo_sensor import TipoSensor
from app.repositories.base import BaseRepository


class TipoSensorRepository(BaseRepository[TipoSensor]):
    modelo = TipoSensor

    def obtener_por_clave(self, clave: str) -> TipoSensor | None:
        return self.db.scalar(select(TipoSensor).where(TipoSensor.clave == clave))

    def mapa_por_clave(self) -> dict[str, TipoSensor]:
        """Devuelve {clave: TipoSensor} para resolver lotes sin N consultas."""
        return {t.clave: t for t in self.db.scalars(select(TipoSensor))}
