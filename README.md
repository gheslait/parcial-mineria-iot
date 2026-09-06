# Parcial Integrador — Minería de Datos IoT
### Sistema de monitoreo de riesgo de combustión / incendio

Solución de analítica de datos IoT: captura con ESP32 (sensores **MQ7** — monóxido de carbono —
y **humedad de suelo resistiva**) → **API REST (FastAPI)** → **PostgreSQL + TimescaleDB** →
**Streamlit** (EDA + Machine Learning) → **Power BI**.

> El monóxido de carbono es un producto de la combustión incompleta (indicador temprano de fuego
> latente); el suelo/hojarasca seco eleva el riesgo de ignición. El **índice de riesgo** combina
> CO alto + humedad baja + tendencia.

## Estructura del repositorio

| Carpeta | Contenido | Fase |
|---|---|---|
| `api/` | API REST FastAPI (POO por capas) + migraciones SQL + simulador del ESP32 | Fase 2 (20%) |
| `streamlit_app/` | Aplicación analítica: exploración, EDA, anomalías, 2 modelos de ML | Fase 3 (25%) |
| `docs/` | Arquitectura, modelo de datos (DER), contrato de la API, checklist de rúbrica | — |

Firmware del ESP32 y circuito (Fase 1), dashboard `.pbix` (Fase 4) y sustentación (Fase 5) los
cubren otros integrantes. La API deja el endpoint de ingesta y las vistas de BD listos para ellos.

## Puesta en marcha rápida

```bash
# 1. API + Base de datos
cd api
python -m venv .venv && .venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env                                 # y editar con la cadena real
python scripts/init_db.py                               # crea schema, 9 tablas, hypertable, vistas, seeds
python scripts/seed_historico.py --dias 20              # histórico simulado para EDA/ML/Power BI
uvicorn app.main:app --reload                           # http://localhost:8000/docs

# 2. Simulador del ESP32 (en otra terminal, opcional)
python scripts/simulador.py --http --intervalo 5

# 3. Aplicación Streamlit
cd ../streamlit_app
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py                                    # http://localhost:8501
```

## Flujo de datos

```
ESP32  --HTTP POST JSON-->  API (valida tipo/rango/formato)  -->  PostgreSQL + TimescaleDB
                                                                       |
                                              Streamlit (lectura) <----+----> Power BI (lectura)
```

Ver `docs/ARQUITECTURA.md` y `docs/RUBRICA.md`.
