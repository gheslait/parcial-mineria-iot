"""Detector 1 — fuera del rango físico declarado del sensor."""
from __future__ import annotations

from app.services.anomalias.base import Anomalia, Contexto, DetectorAnomalias


class DetectorRangoFisico(DetectorAnomalias):
    nombre = "rango_fisico"

    def detectar(self, valor: float, ctx: Contexto) -> Anomalia | None:
        if ctx.rango_min <= valor <= ctx.rango_max:
            return None
        # score = cuánto se sale, normalizado por la amplitud del rango
        amplitud = max(ctx.rango_max - ctx.rango_min, 1e-9)
        exceso = (
            ctx.rango_min - valor if valor < ctx.rango_min else valor - ctx.rango_max
        )
        return Anomalia(
            metodo=self.nombre,
            valor=valor,
            score=round(exceso / amplitud, 4),
            descripcion=(
                f"{ctx.clave_tipo}: {valor} fuera del rango físico "
                f"[{ctx.rango_min}, {ctx.rango_max}]"
            ),
        )
