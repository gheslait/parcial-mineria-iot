"""
Índice de riesgo de combustión (0–100).

Combina tres señales del dominio:

* **CO (MQ7)**  — más ppm ⇒ más riesgo (producto de combustión incompleta).
* **Humedad del suelo** — menos % ⇒ más riesgo (material seco se enciende antes).
* **Tendencia del CO** — si el CO viene subiendo, agrava el riesgo.

Es determinístico y explicable (útil para etiquetar el histórico y entrenar el
clasificador de la Fase 3).
"""
from __future__ import annotations

from dataclasses import dataclass

# Pesos de cada componente (suman 1.0)
_W_CO = 0.5
_W_HUMEDAD = 0.35
_W_TENDENCIA = 0.15

# Puntos de referencia para normalizar a 0–100
_CO_SEGURO_PPM = 9.0        # OMS: 9 ppm promedio 8h
_CO_CRITICO_PPM = 100.0     # combustión activa cercana
_HUM_CRITICA = 12.0         # suelo muy seco
_HUM_SEGURA = 45.0          # suelo con humedad suficiente
_TEND_CRITICA_PPM_MIN = 5.0  # subida de CO que satura el componente de tendencia

NIVELES = ("bajo", "medio", "alto", "critico")


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _rampa(valor: float, v0: float, v1: float) -> float:
    """Lineal: v0 → 0, v1 → 100, saturada fuera del intervalo."""
    if v1 == v0:
        return 0.0
    return _clip((valor - v0) / (v1 - v0) * 100.0)


@dataclass(frozen=True)
class Desglose:
    score: float
    nivel: str
    componente_co: float
    componente_humedad: float
    componente_tendencia: float


class IndiceRiesgo:
    """Calcula el índice a partir de los valores actuales y la tendencia del CO."""

    def calcular(
        self,
        *,
        co_ppm: float | None,
        humedad_pct: float | None,
        tendencia_co_ppm_min: float = 0.0,
    ) -> Desglose:
        comp_co = _rampa(co_ppm, _CO_SEGURO_PPM, _CO_CRITICO_PPM) if co_ppm is not None else 0.0
        # Humedad: rampa invertida (menos humedad ⇒ mayor componente)
        comp_hum = (
            100.0 - _rampa(humedad_pct, _HUM_CRITICA, _HUM_SEGURA)
            if humedad_pct is not None
            else 0.0
        )
        comp_tend = _rampa(max(tendencia_co_ppm_min, 0.0), 0.0, _TEND_CRITICA_PPM_MIN)

        score = _clip(_W_CO * comp_co + _W_HUMEDAD * comp_hum + _W_TENDENCIA * comp_tend)
        return Desglose(
            score=round(score, 2),
            nivel=self.nivel_desde_score(score),
            componente_co=round(comp_co, 2),
            componente_humedad=round(comp_hum, 2),
            componente_tendencia=round(comp_tend, 2),
        )

    @staticmethod
    def nivel_desde_score(score: float) -> str:
        if score >= 75:
            return "critico"
        if score >= 50:
            return "alto"
        if score >= 25:
            return "medio"
        return "bajo"
