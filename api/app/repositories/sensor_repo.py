"""Repositorio de `Sensor`."""
from __future__ import annotations

from sqlalchemy import select

from app.models.sensor import Sensor
from app.repositories.base import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    modelo = Sensor

    def obtener(self, id_: int) -> Sensor | None:  # type: ignore[override]
        return self.db.get(Sensor, id_)

    def por_dispositivo(self, id_dispositivo: int) -> list[Sensor]:
        return list(
            self.db.scalars(select(Sensor).where(Sensor.id_dispositivo == id_dispositivo))
        )

    def resolver(self, id_dispositivo: int, id_tipo_sensor: int) -> Sensor | None:
        """El sensor de ese tipo montado en ese dispositivo (UNIQUE en BD)."""
        return self.db.scalar(
            select(Sensor).where(
                Sensor.id_dispositivo == id_dispositivo,
                Sensor.id_tipo_sensor == id_tipo_sensor,
            )
        )

    def obtener_o_crear(
        self, id_dispositivo: int, id_tipo_sensor: int, *, etiqueta: str
    ) -> Sensor:
        existente = self.resolver(id_dispositivo, id_tipo_sensor)
        if existente:
            return existente
        return self.crear(
            Sensor(
                id_dispositivo=id_dispositivo,
                id_tipo_sensor=id_tipo_sensor,
                etiqueta=etiqueta,
            )
        )
