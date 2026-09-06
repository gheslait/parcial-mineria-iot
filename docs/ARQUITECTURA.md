# Arquitectura — API (Fase 2)

La API está organizada en **capas con responsabilidad única**. Cada petición
baja por las capas y ninguna capa salta a otra que no sea su vecina.

```
Cliente (ESP32 / Streamlit / Power BI / navegador)
        │  HTTP + JSON
        ▼
routers/        (FastAPI)      valida forma HTTP, (de)serializa, traduce errores
        ▼
schemas/        (Pydantic v2)  VALIDACIÓN nivel 1: tipo, formato, techos absolutos
        ▼
services/       (dominio)      reglas de negocio, orquestación, sin SQL
   ├── validacion_service      VALIDACIÓN nivel 2: rango físico vs. tipo_sensor
   ├── ingesta_service         caso de uso central (compone todo lo demás)
   ├── riesgo/                 índice compuesto + motor de reglas de combustión
   └── anomalias/              ABC + 3 detectores (z-score, IQR, rango físico)
        ▼
repositories/   (patrón Repository)   TODO el SQL/ORM; una clase por entidad
        ▼
models/         (SQLAlchemy ORM)      9 tablas, 1 archivo por tabla
        ▼
core/database.py  → Engine único (pool) → PostgreSQL + TimescaleDB
```

## Principios de POO aplicados

| Concepto | Dónde |
|---|---|
| **Herencia** | `Base` declarativa + `mixins.py` (`PkEnteraMixin`, `PkGrandeMixin`, `TimestampMixin`) en los 9 modelos · `BaseRepository[T]` genérico con 9 subclases · `DetectorAnomalias` (ABC) → 3 clases · `ModeloPrediccion` (ABC) → 2 clases · `SimuladorSensor` (ABC) → 2 clases |
| **Polimorfismo** | `for det in DETECTORES: det.detectar(valor, ctx)` — misma interfaz, tres estrategias · modelos de ML intercambiables por `entrenar/predecir` |
| **Encapsulación** | el SQL vive solo en `repositories/`; las reglas solo en `services/`; los `routers/` solo hablan HTTP |
| **Abstracción** | `abc.ABC` + `@abstractmethod` en detectores, modelos y simuladores |
| **Composición** | `IngestaService` compone `ValidacionService`, `EvaluadorRiesgo`, los detectores y 8 repositorios |

## Flujo de `POST /api/v1/ingesta`

1. `routers/ingesta.py` recibe el JSON. FastAPI lo valida contra
   `schemas/ingesta.py::PayloadESP32` → **nivel 1** (tipo `float`/`datetime`,
   código con regex, timestamp no futuro, sin tipos repetidos, techo absoluto).
   Si falla → `422` automático.
2. `IngestaService.procesar()`:
   - `DispositivoRepository.obtener_por_codigo()` → `404` si no existe.
   - por cada lectura: `ValidacionService.validar()` → **nivel 2** (compara con
     `tipo_sensor.rango_min/max`: dentro = `valida`; leve exceso = `sospechosa`;
     exceso burdo = `ErrorValidacion` → `422`).
   - `SensorRepository.obtener_o_crear()` resuelve el sensor físico.
   - `LecturaRepository.crear()` inserta en la hypertable.
   - los 3 detectores de `services/anomalias` corren sobre la ventana reciente;
     los positivos se guardan en `anomalia`.
   - `EvaluadorRiesgo.evaluar()` combina el índice compuesto (CO ↑ + humedad ↓ +
     tendencia) con las `regla_riesgo` activas; si el nivel ≥ `medio` crea un
     `evento_riesgo`.
   - si vino `estado`, se guarda un `estado_dispositivo` (heartbeat).
3. El router hace `db.commit()` (o `rollback()` ante excepción) y responde `201`
   con el resumen.

## Estrategia de errores

`core/exceptions.py` define excepciones de dominio con `codigo_http`. Un único
`@app.exception_handler(ErrorDominio)` en `main.py` las traduce. Los
services/repositories nunca importan FastAPI.
