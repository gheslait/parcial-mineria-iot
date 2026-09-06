"""Esquemas de salida para `evento_riesgo` y `anomalia`."""
from __future__ import annotations

from datetime import datetime

from app.schemas.base import EsquemaORM


class EventoRiesgoOut(EsquemaORM):
    id: int
    id_dispositivo: int
    id_regla: int | None
    nivel: str
    score: float
    valor_mq7: float | None
    valor_humedad: float | None
    mensaje: str
    estado: str
    detectado_en: datetime
    cerrado_en: datetime | None


class AnomaliaOut(EsquemaORM):
    id: int
    id_sensor: int
    id_lectura: int | None
    metodo: str
    valor: float
    score: float
    descripcion: str
    detectado_en: datetime
