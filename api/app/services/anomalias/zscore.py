"""Detector 2 — z-score sobre la ventana reciente del sensor."""
from __future__ import annotations

import numpy as np

from app.services.anomalias.base import Anomalia, Contexto, DetectorAnomalias

_MIN_MUESTRAS = 15


class DetectorZScore(DetectorAnomalias):
    nombre = "zscore"

    def __init__(self, umbral: float = 3.5) -> None:
        self.umbral = umbral

    def detectar(self, valor: float, ctx: Contexto) -> Anomalia | None:
        hist = np.asarray(ctx.historico, dtype=float)
        if hist.size < _MIN_MUESTRAS:
            return None
        mu = float(hist.mean())
        sigma = float(hist.std(ddof=1))
        if sigma < 1e-9:
            return None
        z = (valor - mu) / sigma
        if abs(z) < self.umbral:
            return None
        return Anomalia(
            metodo=self.nombre,
            valor=valor,
            score=round(abs(z), 4),
            descripcion=(
                f"{ctx.clave_tipo}: z={z:.2f} (media {mu:.2f}, σ {sigma:.2f}, "
                f"umbral {self.umbral})"
            ),
        )
