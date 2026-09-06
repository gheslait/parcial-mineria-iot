"""
Simulación de los sensores del grupo (MQ7 + humedad de suelo).

POO: `SimuladorSensor` es abstracto; `SimuladorMQ7` y `SimuladorHumedadSuelo`
son estrategias concretas. `EscenarioRiesgo` compone ambos y programa episodios
correlacionados (sequía + rampa de CO). `InyectorAnomalias` corrompe una
fracción de las lecturas para poder probar la detección de atípicos.
"""
from app.simulacion.escenario import EscenarioRiesgo, InyectorAnomalias, LecturaSimulada
from app.simulacion.sensores import (
    SimuladorHumedadSuelo,
    SimuladorMQ7,
    SimuladorSensor,
)

__all__ = [
    "EscenarioRiesgo",
    "InyectorAnomalias",
    "LecturaSimulada",
    "SimuladorHumedadSuelo",
    "SimuladorMQ7",
    "SimuladorSensor",
]
