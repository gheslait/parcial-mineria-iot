"""
Contrato de ingesta del ESP32  —  `POST /api/v1/ingesta`.

Aquí vive la **validación de tipo y formato** (nivel 1). La validación de
**rango físico** contra `tipo_sensor` (nivel 2) la hace `ValidacionService`.

Payload esperado:

    {
      "codigo_dispositivo": "ESP32-COMB-01",
      "enviado_en": "2026-09-05T14:03:11-05:00",
      "lecturas": [
        {"tipo_sensor": "MQ7",       "valor": 8.4,  "unidad": "ppm", "crudo": 1720},
        {"tipo_sensor": "HUM_SUELO", "valor": 23.1, "unidad": "%"}
      ],
      "estado": {"wifi_rssi": -63, "memoria_libre": 90112, "uptime_seg": 3600,
                 "envio_ok": true, "mensaje_lcd": "CO 8.4ppm H 23%"}
    }
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator, model_validator

from app.schemas.base import EsquemaBase

CodigoDispositivo = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{3,40}$")
]
ClaveTipoSensor = Annotated[
    str, StringConstraints(pattern=r"^[A-Z0-9_]{2,20}$")
]

# Techos absolutos de cordura (nivel 1): límites de imposibilidad física del
# transductor, más holgados que el rango de calibración. El rango real y la
# banda "sospechosa" se validan contra `tipo_sensor` en `ValidacionService`.
TECHOS_ABSOLUTOS: dict[str, tuple[float, float]] = {
    "MQ7": (-50.0, 10000.0),     # ppm de CO
    "HUM_SUELO": (-5.0, 150.0),  # % de humedad
}
_MARGEN_FUTURO = timedelta(minutes=5)
_ANTIGUEDAD_MAX = timedelta(days=3)


class LecturaIngesta(EsquemaBase):
    tipo_sensor: ClaveTipoSensor
    valor: float
    unidad: str | None = Field(default=None, max_length=15)
    crudo: float | None = None
    medido_en: datetime | None = None  # si falta, se usa `enviado_en` del lote

    @field_validator("valor", "crudo")
    @classmethod
    def _finito(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("el valor debe ser un número finito (no NaN/Inf)")
        return v

    @model_validator(mode="after")
    def _techo_absoluto(self) -> "LecturaIngesta":
        techo = TECHOS_ABSOLUTOS.get(self.tipo_sensor)
        if techo and not (techo[0] <= self.valor <= techo[1]):
            raise ValueError(
                f"{self.tipo_sensor}: valor {self.valor} fuera del techo absoluto {techo}"
            )
        return self


class EstadoIngesta(EsquemaBase):
    wifi_rssi: int | None = Field(default=None, ge=-120, le=0)
    memoria_libre: int | None = Field(default=None, ge=0)
    uptime_seg: int | None = Field(default=None, ge=0)
    envio_ok: bool = True
    mensaje_lcd: str | None = Field(default=None, max_length=64)


class PayloadESP32(EsquemaBase):
    codigo_dispositivo: CodigoDispositivo
    enviado_en: datetime
    lecturas: list[LecturaIngesta] = Field(min_length=1, max_length=20)
    estado: EstadoIngesta | None = None

    @field_validator("enviado_en")
    @classmethod
    def _timestamp_plausible(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        ahora = datetime.now(timezone.utc)
        if v > ahora + _MARGEN_FUTURO:
            raise ValueError("enviado_en está en el futuro")
        if v < ahora - _ANTIGUEDAD_MAX:
            raise ValueError("enviado_en es demasiado antiguo (> 3 días)")
        return v

    @model_validator(mode="after")
    def _sin_tipos_repetidos(self) -> "PayloadESP32":
        claves = [le.tipo_sensor for le in self.lecturas]
        if len(claves) != len(set(claves)):
            raise ValueError("hay tipos de sensor repetidos en el mismo lote")
        return self


class ResultadoLectura(EsquemaBase):
    tipo_sensor: str
    valor: float
    calidad: str
    id_lectura: int | None = None


class RespuestaIngesta(EsquemaBase):
    dispositivo: str
    recibidas: int
    almacenadas: int
    resultados: list[ResultadoLectura]
    anomalias_detectadas: int
    evento_riesgo: dict | None = None
