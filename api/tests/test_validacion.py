"""Validación de nivel 2: rango físico contra el catálogo `tipo_sensor`."""
from types import SimpleNamespace

import pytest

from app.core.exceptions import ErrorValidacion
from app.schemas.ingesta import LecturaIngesta
from app.services.validacion_service import ValidacionService


def _catalogo():
    mq7 = SimpleNamespace(clave="MQ7", unidad="ppm", rango_min=0, rango_max=1000)
    hum = SimpleNamespace(clave="HUM_SUELO", unidad="%", rango_min=0, rango_max=100)
    return {"MQ7": mq7, "HUM_SUELO": hum}


@pytest.fixture
def servicio():
    return ValidacionService()


def test_valor_en_rango_es_valida(servicio):
    r = servicio.validar(LecturaIngesta(tipo_sensor="MQ7", valor=12.0), _catalogo())
    assert r.calidad == "valida"


def test_ligeramente_fuera_es_sospechosa(servicio):
    # rango 0..100, exceso 5 <= 10 % de la amplitud -> se almacena, marcada
    r = servicio.validar(LecturaIngesta(tipo_sensor="HUM_SUELO", valor=105.0), _catalogo())
    assert r.calidad == "sospechosa"


def test_muy_fuera_de_rango_rechazado(servicio):
    with pytest.raises(ErrorValidacion):
        servicio.validar(LecturaIngesta(tipo_sensor="HUM_SUELO", valor=140.0), _catalogo())


def test_tipo_desconocido_rechazado(servicio):
    with pytest.raises(ErrorValidacion):
        servicio.validar(LecturaIngesta(tipo_sensor="XYZ", valor=1.0), _catalogo())


def test_unidad_incorrecta_rechazada(servicio):
    with pytest.raises(ErrorValidacion):
        servicio.validar(
            LecturaIngesta(tipo_sensor="MQ7", valor=10.0, unidad="mg/L"), _catalogo()
        )
