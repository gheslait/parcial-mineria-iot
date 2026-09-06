"""Evaluación del riesgo de combustión (índice compuesto + motor de reglas)."""
from app.services.riesgo.evaluador import EvaluadorRiesgo, ResultadoRiesgo
from app.services.riesgo.indice import IndiceRiesgo

__all__ = ["EvaluadorRiesgo", "IndiceRiesgo", "ResultadoRiesgo"]
