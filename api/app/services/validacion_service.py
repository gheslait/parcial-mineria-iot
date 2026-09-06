"""
`ValidacionService` — validación de nivel 2 (rango físico y coherencia con el catálogo).

Nivel 1 (tipo, formato, techo absoluto) ya lo hizo Pydantic en `schemas/ingesta.py`.
Aquí se compara contra `tipo_sensor.rango_min/max` de la BASE DE DATOS y se decide
la `calidad` de la lectura:

* dentro de rango                         -> "valida"
* fuera de rango pero cerca (< 10 %)       -> "sospechosa"  (se almacena, se marca)
* fuera de rango de forma burda            -> ErrorValidacion (HTTP 422, no se almacena)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import ErrorValidacion
from app.models.tipo_sensor import TipoSensor
from app.schemas.ingesta import LecturaIngesta

_TOLERANCIA_SOSPECHOSA = 0.10  # 10 % de la amplitud del rango
_UNIDADES_ESPERADAS = {"MQ7": "ppm", "HUM_SUELO": "%"}


@dataclass(frozen=True)
class LecturaValidada:
    tipo_sensor: TipoSensor
    valor: float
    unidad: str
    crudo: float | None
    calidad: str


class ValidacionService:
    def validar(
        self, entrada: LecturaIngesta, catalogo: dict[str, TipoSensor]
    ) -> LecturaValidada:
        tipo = catalogo.get(entrada.tipo_sensor)
        if tipo is None:
            raise ErrorValidacion(
                f"tipo de sensor desconocido: {entrada.tipo_sensor!r}", campo="tipo_sensor"
            )

        unidad = entrada.unidad or _UNIDADES_ESPERADAS.get(entrada.tipo_sensor, tipo.unidad)
        esperada = _UNIDADES_ESPERADAS.get(entrada.tipo_sensor)
        if esperada and unidad != esperada:
            raise ErrorValidacion(
                f"{entrada.tipo_sensor}: unidad {unidad!r}, se esperaba {esperada!r}",
                campo="unidad",
            )

        rmin, rmax = float(tipo.rango_min), float(tipo.rango_max)
        amplitud = max(rmax - rmin, 1e-9)
        valor = float(entrada.valor)

        if rmin <= valor <= rmax:
            calidad = "valida"
        else:
            exceso = (rmin - valor) if valor < rmin else (valor - rmax)
            if exceso <= _TOLERANCIA_SOSPECHOSA * amplitud:
                calidad = "sospechosa"
            else:
                raise ErrorValidacion(
                    f"{entrada.tipo_sensor}: {valor} {unidad} fuera del rango físico "
                    f"[{rmin}, {rmax}]",
                    campo="valor",
                )

        return LecturaValidada(
            tipo_sensor=tipo, valor=valor, unidad=unidad, crudo=entrada.crudo, calidad=calidad
        )
