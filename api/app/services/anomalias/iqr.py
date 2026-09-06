"""Detector 3 — regla del rango intercuartílico (IQR / Tukey)."""
from __future__ import annotations

import numpy as np

from app.services.anomalias.base import Anomalia, Contexto, DetectorAnomalias

_MIN_MUESTRAS = 20


class DetectorIQR(DetectorAnomalias):
    nombre = "iqr"

    def __init__(self, factor: float = 3.0) -> None:
        self.factor = factor

    def detectar(self, valor: float, ctx: Contexto) -> Anomalia | None:
        hist = np.asarray(ctx.historico, dtype=float)
        if hist.size < _MIN_MUESTRAS:
            return None
        q1, q3 = np.percentile(hist, [25, 75])
        iqr = float(q3 - q1)
        if iqr < 1e-9:
            return None
        low, high = q1 - self.factor * iqr, q3 + self.factor * iqr
        if low <= valor <= high:
            return None
        distancia = (low - valor if valor < low else valor - high) / iqr
        return Anomalia(
            metodo=self.nombre,
            valor=valor,
            score=round(float(distancia), 4),
            descripcion=(
                f"{ctx.clave_tipo}: fuera de [{low:.2f}, {high:.2f}] "
                f"(IQR={iqr:.2f}, factor {self.factor})"
            ),
        )
