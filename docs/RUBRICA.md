# Checklist de rúbrica — Fases 2 y 3

Para revisar punto por punto en la sustentación. (Fases 1, 4 y 5 son de otros
integrantes.)

## Fase 2 — API y base de datos (20 %)

| Requisito | Estado | Evidencia |
|---|---|---|
| API REST en Flask **o FastAPI** | ✅ | FastAPI — `api/app/main.py` |
| **Estructura POO** con distribución de carpetas y archivos | ✅ | `api/app/{core,models,schemas,repositories,services,routers}` — ver `docs/ARQUITECTURA.md` |
| Herencia / polimorfismo / encapsulación / abstracción / composición | ✅ | `BaseRepository[T]`, mixins ORM, `DetectorAnomalias` (ABC)+3, `ModeloPrediccion` (ABC)+2, `SimuladorSensor` (ABC)+2 |
| Recibe datos del ESP32 por **HTTP POST JSON** | ✅ | `POST /api/v1/ingesta` |
| Valida **tipo** | ✅ | Pydantic (`float`, `datetime`, enums) |
| Valida **formato** | ✅ | regex de `codigo_dispositivo` y `tipo_sensor`, ISO-8601, `field_validator` |
| Valida **rango** | ✅ | 2 niveles: `Field`/techo absoluto (Pydantic) + `ValidacionService` vs `tipo_sensor.rango_min/max` |
| **PostgreSQL** | ✅ | servidor `gheslait.com:15432`, base `timescaledb`, schema `combustion_riesgo` |
| Extensión **TIMESCALEDB** | ✅ | `migrations/002_timescale.sql`: `create_hypertable('lectura')`, agregado continuo `ca_lecturas_15min`, compresión. `GET /health` lo confirma |
| **timestamp** en los datos | ✅ | `lectura.medido_en timestamptz` (columna de partición) |
| **Identificación de grupo/dispositivo** | ✅ | `lectura → dispositivo → grupo`; `dispositivo.codigo` único |
| **Mínimo 7 tablas relacionadas** | ✅ **9 tablas** | `docs/MODELO_DATOS.md` (DER + diccionario) |
| Identifica valores **atípicos/anómalos** | ✅ | tabla `anomalia` + `services/anomalias/` (z-score, IQR, rango físico) |
| Funcionamiento óptimo | ✅ | `pytest` (23 pruebas), índices por `(sensor, tiempo)`, pool de conexiones, agregado continuo |

## Fase 3 — Analítica en Streamlit (25 %)

| Requisito | Estado | Evidencia |
|---|---|---|
| App interactiva en **Streamlit** | ✅ | `streamlit_app/app.py` (4 páginas) |
| Explorar histórico con **filtros dinámicos de fecha** | ✅ | `st.date_input` en la barra lateral (`vistas/comun.py`) |
| Filtro dinámico de **rango de valores** | ✅ | `st.slider` "rango de valores" |
| Filtro dinámico de **variable** | ✅ | `st.multiselect` de variables + `selectbox` de dispositivo y calidad |
| **EDA** (comportamiento, distribución, calidad) | ✅ | `vistas/eda.py` + `dominio/eda.py`: describe, asimetría/curtosis, histogramas, boxplots, faltantes por día, estacionalidad horaria |
| **Matriz de correlación** | ✅ | `AnalizadorEDA.matriz_correlacion` (pearson/spearman) + heatmap + correlación cruzada CO↔humedad |
| **Limpieza básica** | ✅ | `dominio/limpieza.py::LimpiadorDatos`: duplicados, fuera de rango físico, interpolación, resampleo; con bitácora |
| **Dos algoritmos de Machine Learning** | ✅ | `RegresorCO` (RandomForestRegressor → pronóstico de CO) y `ClasificadorRiesgo` (RandomForestClassifier → nivel de riesgo). Ambos bajo la ABC `ModeloPrediccion` |
| Métricas de los modelos | ✅ | Regresión: MAE, RMSE, R². Clasificación: accuracy, balanced accuracy, F1 macro, matriz de confusión, importancia de variables |
| Identificar valores **atípicos** | ✅ | `vistas/anomalias.py` + `dominio/anomalias.py::DetectorAtipicos` (z-score + IQR) y además las anomalías que registró la API |
| Aplicativo **dinámico**, interactuar con cada variable | ✅ | 4 páginas reactivas, controles en cada vista, `st.cache_data` |
| Conexión **directa a PostgreSQL** (sin cargar datos a mano) | ✅ | `core/db.py::RepositorioLecturas` (SELECT), vistas `vw_lecturas_enriquecidas` / `vw_riesgo_por_hora` |

## Cómo demostrarlo (5 min)

1. `GET /health` → `timescaledb: true`.
2. `psql`: `\dt combustion_riesgo.*` (9) · `SELECT * FROM timescaledb_information.hypertables;`
3. `POST /api/v1/ingesta` con un valor fuera de rango → `422` con detalle.
4. `python scripts/simulador.py --http --intervalo 5` → llegan lecturas, se ve `RIESGO=` cuando sube el CO.
5. Streamlit: cambiar fechas/variable/rango → todo reacciona; pestaña **Predicción** → métricas de los 2 modelos + simulador de riesgo.
6. Power BI (compañero) abre la misma BD y ve tablas + vistas.
