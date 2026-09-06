"""Simuladores de sensor (estrategias concretas de `SimuladorSensor`)."""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from datetime import datetime


class SimuladorSensor(ABC):
    """Genera una serie temporal plausible para una magnitud."""

    clave: str
    unidad: str

    def __init__(self, *, semilla: int | None = None) -> None:
        self._rng = random.Random(semilla)

    @abstractmethod
    def medir(self, t: datetime, *, intensidad_evento: float = 0.0) -> float:
        """
        Valor en el instante `t`.

        `intensidad_evento` ∈ [0, 1] lo fija el `EscenarioRiesgo`: 0 = condición
        normal, 1 = episodio de riesgo de combustión en su punto máximo.
        """
        raise NotImplementedError

    def convertir_crudo(self, valor: float) -> float:
        """Aproxima la lectura ADC (0–4095) que habría entregado el ESP32."""
        return round(valor, 2)


class SimuladorMQ7(SimuladorSensor):
    """Monóxido de carbono (ppm). Sube fuerte durante un episodio de combustión."""

    clave = "MQ7"
    unidad = "ppm"

    def __init__(self, *, base_ppm: float = 6.0, semilla: int | None = None) -> None:
        super().__init__(semilla=semilla)
        self._base = base_ppm
        self._deriva = 0.0

    def medir(self, t: datetime, *, intensidad_evento: float = 0.0) -> float:
        # ciclo diario suave (tránsito/actividad de día)
        hora = t.hour + t.minute / 60
        diurno = 2.0 * math.sin((hora - 6) / 24 * 2 * math.pi)
        # camino aleatorio acotado
        self._deriva = max(-2.0, min(2.0, self._deriva + self._rng.gauss(0, 0.15)))
        ruido = self._rng.gauss(0, 0.6)
        # el evento agrega hasta ~120 ppm de forma no lineal
        aporte_evento = 120.0 * (intensidad_evento ** 1.5)
        valor = self._base + diurno + self._deriva + ruido + aporte_evento
        return round(max(0.0, valor), 2)

    def convertir_crudo(self, valor: float) -> float:
        return round(min(4095, valor / 1000 * 4095), 0)


class SimuladorHumedadSuelo(SimuladorSensor):
    """Humedad de suelo resistiva (%). Baja durante sequías / episodios de riesgo."""

    clave = "HUM_SUELO"
    unidad = "%"

    def __init__(self, *, base_pct: float = 38.0, semilla: int | None = None) -> None:
        super().__init__(semilla=semilla)
        self._nivel = base_pct
        self._base = base_pct

    def medir(self, t: datetime, *, intensidad_evento: float = 0.0) -> float:
        # secado lento + recuperación hacia la base; lluvia ocasional
        secado = 0.02 + 0.25 * intensidad_evento
        recuperacion = 0.01 * (self._base - self._nivel)
        lluvia = 6.0 if self._rng.random() < 0.002 else 0.0
        self._nivel += -secado + recuperacion + lluvia + self._rng.gauss(0, 0.2)
        self._nivel = max(3.0, min(95.0, self._nivel))
        return round(self._nivel, 2)

    def convertir_crudo(self, valor: float) -> float:
        # sonda resistiva: más humedad => menor resistencia => menor ADC
        return round(4095 - valor / 100 * 4095, 0)
