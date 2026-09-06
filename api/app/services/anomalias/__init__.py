"""
Detección de valores atípicos.

`DetectorAnomalias` es una clase abstracta; hay tres implementaciones
intercambiables (polimorfismo). `DETECTORES` es la lista que recorre el
`IngestaService` para cada lectura nueva.
"""
from app.services.anomalias.base import Anomalia, DetectorAnomalias
from app.services.anomalias.iqr import DetectorIQR
from app.services.anomalias.rango_fisico import DetectorRangoFisico
from app.services.anomalias.zscore import DetectorZScore

#: Detectores aplicados en orden a cada lectura entrante.
DETECTORES: list[DetectorAnomalias] = [
    DetectorRangoFisico(),
    DetectorZScore(umbral=3.5),
    DetectorIQR(factor=3.0),
]

__all__ = [
    "Anomalia",
    "DetectorAnomalias",
    "DetectorIQR",
    "DetectorRangoFisico",
    "DetectorZScore",
    "DETECTORES",
]
