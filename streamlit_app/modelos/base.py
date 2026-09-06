"""
`ModeloPrediccion` — interfaz común de los dos algoritmos de ML (Fase 3).

Herencia + polimorfismo: la vista de predicción entrena y evalúa cualquier
modelo a través de estos métodos, sin conocer su implementación.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ResultadoEntrenamiento:
    metricas: dict[str, float]
    y_test: pd.Series
    y_pred: pd.Series
    importancias: pd.Series | None = None
    extra: dict = field(default_factory=dict)


class ModeloPrediccion(ABC):
    #: nombre legible para la interfaz
    nombre: str = "modelo"
    #: 'regresion' | 'clasificacion'
    tipo: str = "regresion"

    def __init__(self, **hiperparametros) -> None:
        self.hiperparametros = hiperparametros
        self._entrenado = False
        self.resultado: ResultadoEntrenamiento | None = None

    @abstractmethod
    def construir_features(self, df_ancho: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Devuelve (X, y) a partir de la serie ancha limpia."""

    @abstractmethod
    def entrenar(self, df_ancho: pd.DataFrame) -> ResultadoEntrenamiento:
        """Entrena y evalúa con partición temporal; guarda `self.resultado`."""

    @abstractmethod
    def predecir(self, X: pd.DataFrame) -> pd.Series:
        ...

    @property
    def entrenado(self) -> bool:
        return self._entrenado
