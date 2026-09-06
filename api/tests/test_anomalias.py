"""Detectores de anomalías (polimorfismo: misma interfaz, tres estrategias)."""
from app.services.anomalias import DETECTORES, DetectorIQR, DetectorRangoFisico, DetectorZScore
from app.services.anomalias.base import Contexto


def _ctx(hist):
    return Contexto(clave_tipo="MQ7", rango_min=0, rango_max=1000, historico=hist)


def test_rango_fisico_detecta_fuera_de_limite():
    a = DetectorRangoFisico().detectar(1500, _ctx([]))
    assert a is not None and a.metodo == "rango_fisico"


def test_rango_fisico_ignora_valor_normal():
    assert DetectorRangoFisico().detectar(10, _ctx([])) is None


def test_zscore_detecta_pico():
    hist = [10.0 + (i % 3 - 1) * 0.5 for i in range(20)]  # media ~10, sigma ~0.4
    a = DetectorZScore(umbral=3.0).detectar(80.0, _ctx(hist))
    assert a is not None and a.score > 3


def test_zscore_sin_historia_no_dispara():
    assert DetectorZScore().detectar(999, _ctx([1, 2, 3])) is None


def test_iqr_detecta_atipico():
    hist = [10, 11, 9, 10, 12, 8, 11, 10, 9, 10, 11, 10] * 2  # 24 muestras
    a = DetectorIQR(factor=1.5).detectar(40, _ctx(hist))
    assert a is not None and a.metodo == "iqr"


def test_todos_los_detectores_comparten_interfaz():
    ctx = _ctx([10.0] * 30)
    for det in DETECTORES:
        resultado = det.detectar(10.0, ctx)  # valor normal -> nadie dispara
        assert resultado is None
