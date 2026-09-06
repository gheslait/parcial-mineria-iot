"""
Capa de acceso a datos (patrón Repository).

Todo el SQL/ORM vive aquí. Los *services* y *routers* nunca consultan la base
de datos directamente: piden a un repositorio. Cada repositorio concreto hereda
de `BaseRepository[T]` y añade las consultas propias de su entidad.
"""
from app.repositories.anomalia_repo import AnomaliaRepository
from app.repositories.base import BaseRepository
from app.repositories.dispositivo_repo import DispositivoRepository
from app.repositories.estado_dispositivo_repo import EstadoDispositivoRepository
from app.repositories.evento_riesgo_repo import EventoRiesgoRepository
from app.repositories.grupo_repo import GrupoRepository
from app.repositories.lectura_repo import LecturaRepository
from app.repositories.regla_riesgo_repo import ReglaRiesgoRepository
from app.repositories.sensor_repo import SensorRepository
from app.repositories.tipo_sensor_repo import TipoSensorRepository

__all__ = [
    "AnomaliaRepository",
    "BaseRepository",
    "DispositivoRepository",
    "EstadoDispositivoRepository",
    "EventoRiesgoRepository",
    "GrupoRepository",
    "LecturaRepository",
    "ReglaRiesgoRepository",
    "SensorRepository",
    "TipoSensorRepository",
]
