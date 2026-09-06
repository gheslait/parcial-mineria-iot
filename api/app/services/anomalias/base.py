"""Contrato abstracto de un detector de anomalías."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Contexto:
    """Datos que un detector puede necesitar además del valor puntual."""

    clave_tipo: str
    rango_min: float
    rango_max: float
    historico: list[float]   # valores previos del mismo sensor (orden cronológico)


@dataclass(frozen=True)
class Anomalia:
    """Resultado de una detección positiva."""

    metodo: str          # 'zscore' | 'iqr' | 'rango_fisico'
    valor: float
    score: float
    descripcion: str


class DetectorAnomalias(ABC):
    """Interfaz común. Cada estrategia decide si un valor es atípico."""

    #: identificador que se guarda en `anomalia.metodo`
    nombre: str

    @abstractmethod
    def detectar(self, valor: float, ctx: Contexto) -> Anomalia | None:
        """Devuelve una `Anomalia` si `valor` es atípico, o `None`."""
        raise NotImplementedError
