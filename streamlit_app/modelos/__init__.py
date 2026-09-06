from modelos.base import ModeloPrediccion, ResultadoEntrenamiento
from modelos.clasificador_riesgo import ClasificadorRiesgo
from modelos.regresion_co import RegresorCO

#: Los dos algoritmos exigidos por la Fase 3.
MODELOS: dict[str, type[ModeloPrediccion]] = {
    "Regresión — pronóstico de CO (RandomForestRegressor)": RegresorCO,
    "Clasificación — nivel de riesgo (RandomForestClassifier)": ClasificadorRiesgo,
}

__all__ = [
    "ClasificadorRiesgo",
    "MODELOS",
    "ModeloPrediccion",
    "RegresorCO",
    "ResultadoEntrenamiento",
]
