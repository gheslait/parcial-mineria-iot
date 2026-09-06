"""Índice compuesto y motor de reglas de riesgo de combustión."""
from types import SimpleNamespace

from app.services.riesgo import EvaluadorRiesgo, IndiceRiesgo


def test_condicion_segura_es_bajo():
    d = IndiceRiesgo().calcular(co_ppm=5, humedad_pct=50, tendencia_co_ppm_min=0)
    assert d.nivel == "bajo" and d.score < 25


def test_co_alto_y_suelo_seco_eleva_nivel():
    d = IndiceRiesgo().calcular(co_ppm=120, humedad_pct=8, tendencia_co_ppm_min=6)
    assert d.nivel in ("alto", "critico") and d.score >= 50


def test_tendencia_creciente_suma_riesgo():
    sin_t = IndiceRiesgo().calcular(co_ppm=40, humedad_pct=25, tendencia_co_ppm_min=0)
    con_t = IndiceRiesgo().calcular(co_ppm=40, humedad_pct=25, tendencia_co_ppm_min=8)
    assert con_t.score > sin_t.score


def test_regla_simple_evalua_operador():
    regla = SimpleNamespace(operador="ge", umbral_min=50, umbral_max=None)
    from app.models.regla_riesgo import ReglaRiesgo

    r = ReglaRiesgo(operador="ge", umbral_min=50, nombre="x", nivel="alto", mensaje="m")
    assert r.evaluar(60) is True
    assert r.evaluar(40) is False


def test_evaluador_dispara_regla_critica():
    from app.models.regla_riesgo import ReglaRiesgo
    from app.models.tipo_sensor import TipoSensor

    mq7 = TipoSensor(clave="MQ7", nombre="", magnitud="", unidad="ppm", rango_min=0, rango_max=1000)
    regla = ReglaRiesgo(
        id=1, operador="ge", umbral_min=100, nivel="critico", puntaje=40,
        nombre="CO critico", mensaje="riesgo activo",
    )
    regla.tipo_sensor = mq7
    res = EvaluadorRiesgo().evaluar(
        co_ppm=140, humedad_pct=30, tendencia_co_ppm_min=1,
        reglas=[regla], valores_por_clave={"MQ7": 140},
    )
    assert res.nivel == "critico"
    assert res.amerita_evento
    assert "CO critico" in res.reglas_disparadas
