"""Validación de nivel 1 (Pydantic) del payload del ESP32."""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.ingesta import PayloadESP32


def _payload(**over):
    base = {
        "codigo_dispositivo": "ESP32-COMB-01",
        "enviado_en": datetime.now(timezone.utc).isoformat(),
        "lecturas": [
            {"tipo_sensor": "MQ7", "valor": 8.4, "unidad": "ppm"},
            {"tipo_sensor": "HUM_SUELO", "valor": 23.1, "unidad": "%"},
        ],
    }
    base.update(over)
    return base


def test_payload_valido():
    p = PayloadESP32.model_validate(_payload())
    assert len(p.lecturas) == 2


def test_codigo_dispositivo_invalido():
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(_payload(codigo_dispositivo="con espacios!"))


def test_timestamp_futuro_rechazado():
    futuro = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(_payload(enviado_en=futuro))


def test_valor_no_finito_rechazado():
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(
            _payload(lecturas=[{"tipo_sensor": "MQ7", "valor": float("nan")}])
        )


def test_techo_absoluto_mq7():
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(
            _payload(lecturas=[{"tipo_sensor": "MQ7", "valor": 99999}])
        )


def test_tipos_repetidos_rechazados():
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(
            _payload(
                lecturas=[
                    {"tipo_sensor": "MQ7", "valor": 1},
                    {"tipo_sensor": "MQ7", "valor": 2},
                ]
            )
        )


def test_campo_extra_prohibido():
    with pytest.raises(ValidationError):
        PayloadESP32.model_validate(_payload(sospechoso=True))
