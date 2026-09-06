# Contrato de la API

Base URL local: `http://localhost:8000`  ·  Documentación interactiva: `/docs`

Todos los endpoints devuelven JSON. Los errores de dominio salen como
`{"error": "<Tipo>", "detalle": "<mensaje>", "campo": "<opcional>"}`.

## Salud

### `GET /health`
```json
{"status":"ok","postgresql":"17.9","timescaledb":true,
 "timescaledb_version":"2.26.4","schema":"combustion_riesgo"}
```

## Ingesta (escritura) — la usa el ESP32

### `POST /api/v1/ingesta`  → `201`

Cuerpo:
```json
{
  "codigo_dispositivo": "ESP32-COMB-01",
  "enviado_en": "2026-09-05T14:03:11-05:00",
  "lecturas": [
    {"tipo_sensor": "MQ7",       "valor": 8.4,  "unidad": "ppm", "crudo": 1720},
    {"tipo_sensor": "HUM_SUELO", "valor": 23.1, "unidad": "%"}
  ],
  "estado": {"wifi_rssi": -63, "memoria_libre": 90112, "uptime_seg": 3600,
             "envio_ok": true, "mensaje_lcd": "CO 8.4ppm H 23%"}
}
```

Validación aplicada, en orden:

| Nivel | Qué revisa | Falla → |
|---|---|---|
| 1 (Pydantic) | tipos, `codigo_dispositivo` `^[A-Za-z0-9_-]{3,40}$`, `tipo_sensor` `^[A-Z0-9_]{2,20}$`, `valor` finito, `enviado_en` ISO-8601 no futuro y < 3 días, sin tipos repetidos, techo absoluto por magnitud | `422` |
| 2 (`ValidacionService`) | `valor` dentro de `tipo_sensor.rango_min/max`; unidad esperada | dentro → `valida`; exceso ≤ 10 % → `sospechosa`; exceso mayor → `422` |
| negocio | dispositivo existe | `404` |

Respuesta:
```json
{
  "dispositivo": "ESP32-COMB-01",
  "recibidas": 2, "almacenadas": 2,
  "resultados": [
    {"tipo_sensor":"MQ7","valor":8.4,"calidad":"valida","id_lectura":12345},
    {"tipo_sensor":"HUM_SUELO","valor":23.1,"calidad":"valida","id_lectura":12346}
  ],
  "anomalias_detectadas": 0,
  "evento_riesgo": null
}
```

## Consulta (lectura)

| Método | Ruta | Filtros (query) |
|---|---|---|
| GET | `/api/v1/lecturas` | `desde, hasta, tipo_sensor, codigo_dispositivo, valor_min, valor_max, calidad, limite` |
| GET | `/api/v1/lecturas/rango-fechas` | — |
| GET | `/api/v1/eventos-riesgo` | `id_dispositivo, nivel, estado, desde, limite` |
| GET | `/api/v1/anomalias` | `id_sensor, metodo, desde, limite` |
| GET | `/api/v1/grupos` · `/dispositivos` · `/tipos-sensor` · `/sensores` · `/reglas-riesgo` | — |

## Ejemplo de firmware (pseudocódigo ESP32 / MicroPython)

```python
payload = {
    "codigo_dispositivo": CODIGO,
    "enviado_en": iso_utc_now(),
    "lecturas": [
        {"tipo_sensor": "MQ7",       "valor": co_ppm,   "unidad": "ppm", "crudo": adc_mq7},
        {"tipo_sensor": "HUM_SUELO", "valor": hum_pct,  "unidad": "%",   "crudo": adc_hum},
    ],
    "estado": {"wifi_rssi": wifi.rssi(), "envio_ok": True, "mensaje_lcd": lcd_text},
}
urequests.post(API_BASE + "/api/v1/ingesta", json=payload)
```
