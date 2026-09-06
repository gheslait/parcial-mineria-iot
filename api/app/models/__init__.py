"""
Modelos ORM (SQLAlchemy 2.0) — un archivo por tabla.

Importar este paquete registra las 9 tablas en `Base.metadata`, de modo que
`Base.metadata.create_all()` (en `scripts/init_db.py`) las cree todas.

Relaciones (todas por FK salvo `*->lectura`, que es lógica por ser hypertable):

    grupo 1─* dispositivo 1─* sensor 1─* lectura
    tipo_sensor 1─* sensor
    tipo_sensor 1─* regla_riesgo 1─* evento_riesgo *─1 dispositivo
    sensor 1─* anomalia
    dispositivo 1─* estado_dispositivo
"""
from app.models.anomalia import Anomalia
from app.models.dispositivo import Dispositivo
from app.models.estado_dispositivo import EstadoDispositivo
from app.models.evento_riesgo import EventoRiesgo
from app.models.grupo import Grupo
from app.models.lectura import Lectura
from app.models.regla_riesgo import ReglaRiesgo
from app.models.sensor import Sensor
from app.models.tipo_sensor import TipoSensor

__all__ = [
    "Anomalia",
    "Dispositivo",
    "EstadoDispositivo",
    "EventoRiesgo",
    "Grupo",
    "Lectura",
    "ReglaRiesgo",
    "Sensor",
    "TipoSensor",
]
