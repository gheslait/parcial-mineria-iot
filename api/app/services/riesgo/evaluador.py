"""
`EvaluadorRiesgo` — combina el motor de reglas (`regla_riesgo`) con el índice
compuesto (`IndiceRiesgo`) y decide si se genera un `evento_riesgo`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.regla_riesgo import ReglaRiesgo
from app.services.riesgo.indice import IndiceRiesgo, NIVELES

_ORDEN_NIVEL = {n: i for i, n in enumerate(NIVELES)}


@dataclass
class ResultadoRiesgo:
    nivel: str
    score: float
    mensaje: str
    id_regla: int | None = None
    valor_mq7: float | None = None
    valor_humedad: float | None = None
    reglas_disparadas: list[str] = field(default_factory=list)

    @property
    def amerita_evento(self) -> bool:
        return _ORDEN_NIVEL[self.nivel] >= _ORDEN_NIVEL["medio"]


class EvaluadorRiesgo:
    def __init__(self, indice: IndiceRiesgo | None = None) -> None:
        self._indice = indice or IndiceRiesgo()

    def evaluar(
        self,
        *,
        co_ppm: float | None,
        humedad_pct: float | None,
        tendencia_co_ppm_min: float,
        reglas: list[ReglaRiesgo],
        valores_por_clave: dict[str, float],
    ) -> ResultadoRiesgo:
        desglose = self._indice.calcular(
            co_ppm=co_ppm,
            humedad_pct=humedad_pct,
            tendencia_co_ppm_min=tendencia_co_ppm_min,
        )

        nivel = desglose.nivel
        score = desglose.score
        id_regla: int | None = None
        disparadas: list[str] = []
        mensaje = f"Índice compuesto de riesgo de combustión: {score}/100 ({nivel})."

        # Las reglas simples pueden elevar el nivel/score por encima del índice.
        for regla in reglas:
            clave = regla.tipo_sensor.clave if regla.tipo_sensor else None
            if clave is None or clave not in valores_por_clave:
                continue
            if regla.evaluar(valores_por_clave[clave]):
                disparadas.append(regla.nombre)
                score = min(100.0, score + regla.puntaje)
                if _ORDEN_NIVEL[regla.nivel] > _ORDEN_NIVEL[nivel]:
                    nivel, id_regla, mensaje = regla.nivel, regla.id, regla.mensaje

        return ResultadoRiesgo(
            nivel=nivel,
            score=round(score, 2),
            mensaje=mensaje,
            id_regla=id_regla,
            valor_mq7=co_ppm,
            valor_humedad=humedad_pct,
            reglas_disparadas=disparadas,
        )
