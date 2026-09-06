"""
`EscenarioRiesgo` — compone los dos simuladores y programa episodios de riesgo.

Un episodio = ventana de tiempo en la que la humedad cae y el CO sube en forma
de campana (subida, pico, descenso). `InyectorAnomalias` corrompe una fracción
configurable de las lecturas.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.simulacion.sensores import SimuladorHumedadSuelo, SimuladorMQ7, SimuladorSensor


@dataclass(frozen=True)
class LecturaSimulada:
    clave: str
    unidad: str
    valor: float | None      # None = dropout (el ESP32 no reportó)
    crudo: float | None
    anomalia_forzada: str | None = None


@dataclass
class _Episodio:
    inicio: datetime
    duracion: timedelta

    def intensidad(self, t: datetime) -> float:
        if not (self.inicio <= t <= self.inicio + self.duracion):
            return 0.0
        frac = (t - self.inicio) / self.duracion          # 0..1
        return math.sin(frac * math.pi)                    # campana 0->1->0


class InyectorAnomalias:
    """Corrompe lecturas: valor congelado, pico fuera de rango o dropout."""

    def __init__(self, prob: float = 0.02, *, semilla: int | None = None) -> None:
        self.prob = prob
        self._rng = random.Random(semilla)
        self._ultimo: dict[str, float] = {}

    def aplicar(self, clave: str, valor: float) -> tuple[float | None, str | None]:
        self._ultimo[clave] = valor
        if self._rng.random() >= self.prob:
            return valor, None
        tipo = self._rng.choice(["congelado", "pico", "dropout"])
        if tipo == "dropout":
            return None, "dropout"
        if tipo == "congelado":
            return self._ultimo.get(clave, valor), "congelado"
        # pico: fuera del techo físico
        pico = valor * self._rng.choice([-1.5, 3.0, 5.0]) + self._rng.uniform(50, 400)
        return round(pico, 2), "pico"


class EscenarioRiesgo:
    def __init__(
        self,
        *,
        semilla: int = 42,
        prob_anomalia: float = 0.02,
        episodios_por_dia: float = 0.7,
    ) -> None:
        self._rng = random.Random(semilla)
        self.mq7: SimuladorSensor = SimuladorMQ7(semilla=semilla)
        self.humedad: SimuladorSensor = SimuladorHumedadSuelo(semilla=semilla + 1)
        self.inyector = InyectorAnomalias(prob_anomalia, semilla=semilla + 2)
        self._episodios_por_dia = episodios_por_dia
        self._episodios: list[_Episodio] = []
        self._dias_programados: set[int] = set()

    # -- programación de episodios -------------------------------------
    def _asegurar_episodios(self, t: datetime) -> None:
        dia = t.toordinal()
        if dia in self._dias_programados:
            return
        self._dias_programados.add(dia)
        if self._rng.random() < self._episodios_por_dia:
            medianoche = t.replace(hour=0, minute=0, second=0, microsecond=0)
            inicio = medianoche + timedelta(hours=self._rng.uniform(0, 22))
            self._episodios.append(
                _Episodio(inicio=inicio, duracion=timedelta(minutes=self._rng.uniform(25, 120)))
            )

    def intensidad(self, t: datetime) -> float:
        self._asegurar_episodios(t)
        return max((e.intensidad(t) for e in self._episodios), default=0.0)

    # -- generación de lecturas --------------------------------------
    def lecturas_en(self, t: datetime) -> list[LecturaSimulada]:
        inten = self.intensidad(t)
        salida: list[LecturaSimulada] = []
        for sim in (self.mq7, self.humedad):
            base = sim.medir(t, intensidad_evento=inten)
            valor, marca = self.inyector.aplicar(sim.clave, base)
            crudo = sim.convertir_crudo(valor) if valor is not None else None
            salida.append(
                LecturaSimulada(
                    clave=sim.clave,
                    unidad=sim.unidad,
                    valor=valor,
                    crudo=crudo,
                    anomalia_forzada=marca,
                )
            )
        return salida
