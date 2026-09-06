"""
Repositorio de `Lectura` (hypertable).

Además del CRUD heredado, expone consultas de serie temporal con los mismos
filtros dinámicos que usa la app Streamlit (rango de fecha, variable, rango de
valores, calidad).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.dispositivo import Dispositivo
from app.models.lectura import Lectura
from app.models.sensor import Sensor
from app.models.tipo_sensor import TipoSensor
from app.repositories.base import BaseRepository
from app.schemas.lectura import FiltroLecturas


class LecturaRepository(BaseRepository[Lectura]):
    modelo = Lectura

    def filtrar(self, f: FiltroLecturas) -> list[Lectura]:
        stmt = (
            select(Lectura)
            .join(Sensor, Sensor.id == Lectura.id_sensor)
            .join(TipoSensor, TipoSensor.id == Sensor.id_tipo_sensor)
            .join(Dispositivo, Dispositivo.id == Lectura.id_dispositivo)
            .order_by(Lectura.medido_en.desc())
            .limit(f.limite)
        )
        if f.desde:
            stmt = stmt.where(Lectura.medido_en >= f.desde)
        if f.hasta:
            stmt = stmt.where(Lectura.medido_en <= f.hasta)
        if f.tipo_sensor:
            stmt = stmt.where(TipoSensor.clave == f.tipo_sensor)
        if f.codigo_dispositivo:
            stmt = stmt.where(Dispositivo.codigo == f.codigo_dispositivo)
        if f.valor_min is not None:
            stmt = stmt.where(Lectura.valor >= f.valor_min)
        if f.valor_max is not None:
            stmt = stmt.where(Lectura.valor <= f.valor_max)
        if f.calidad:
            stmt = stmt.where(Lectura.calidad == f.calidad)
        return list(self.db.scalars(stmt))

    def ultimas_por_sensor(self, id_sensor: int, n: int = 50) -> list[Lectura]:
        """Ventana reciente para z-score / IQR y para el cálculo de tendencia."""
        stmt = (
            select(Lectura)
            .where(Lectura.id_sensor == id_sensor)
            .order_by(Lectura.medido_en.desc())
            .limit(n)
        )
        return list(self.db.scalars(stmt))[::-1]  # orden cronológico ascendente

    def valor_mas_reciente(self, id_dispositivo: int, clave_tipo: str) -> float | None:
        stmt = (
            select(Lectura.valor)
            .join(Sensor, Sensor.id == Lectura.id_sensor)
            .join(TipoSensor, TipoSensor.id == Sensor.id_tipo_sensor)
            .where(Lectura.id_dispositivo == id_dispositivo, TipoSensor.clave == clave_tipo)
            .order_by(Lectura.medido_en.desc())
            .limit(1)
        )
        v = self.db.scalar(stmt)
        return float(v) if v is not None else None

    def rango_fechas(self) -> tuple[datetime | None, datetime | None]:
        from sqlalchemy import func

        row = self.db.execute(
            select(func.min(Lectura.medido_en), func.max(Lectura.medido_en))
        ).one()
        return row[0], row[1]
