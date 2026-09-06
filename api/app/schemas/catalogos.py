"""Esquemas de salida para las entidades de catálogo / maestras."""
from __future__ import annotations

from datetime import datetime

from app.schemas.base import EsquemaORM


class GrupoOut(EsquemaORM):
    id: int
    nombre: str
    numero: int
    curso: str


class TipoSensorOut(EsquemaORM):
    id: int
    clave: str
    nombre: str
    magnitud: str
    unidad: str
    rango_min: float
    rango_max: float
    precision: float | None
    descripcion: str | None


class DispositivoOut(EsquemaORM):
    id: int
    id_grupo: int
    codigo: str
    descripcion: str | None
    ubicacion: str | None
    activo: bool
    registrado_en: datetime


class SensorOut(EsquemaORM):
    id: int
    id_dispositivo: int
    id_tipo_sensor: int
    etiqueta: str
    pin: str | None
    activo: bool


class ReglaRiesgoOut(EsquemaORM):
    id: int
    id_tipo_sensor: int | None
    nombre: str
    operador: str
    umbral_min: float | None
    umbral_max: float | None
    nivel: str
    puntaje: int
    mensaje: str
    activo: bool
