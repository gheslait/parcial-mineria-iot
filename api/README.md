# API REST — Fase 2

FastAPI + SQLAlchemy ORM + Pydantic v2 · PostgreSQL + TimescaleDB.
Arquitectura por capas (POO): ver [`../docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate en Linux/Mac)
pip install -r requirements.txt
copy .env.example .env             # editar DATABASE_URL con la cadena real
```

## Base de datos

```bash
python scripts/init_db.py                 # schema + 9 tablas + hypertable + vistas + seeds
python scripts/init_db.py --reset         # borra el schema y lo recrea (¡destructivo!)
python scripts/seed_historico.py --dias 20 --limpiar   # histórico simulado para EDA/ML/Power BI
```

## Ejecutar

```bash
uvicorn app.main:app --reload             # http://localhost:8000/docs
```

## Simulador del ESP32

```bash
python scripts/simulador.py --http --intervalo 5          # envía cada 5 s (tiempo real)
python scripts/simulador.py --http --intervalo 2 --acelerar 30 --n 200   # 200 envíos acelerados
```

## Pruebas

```bash
pytest -q        # 23 pruebas de dominio (no requieren base de datos)
```

## Estructura

```
app/
├── core/         config.py · database.py · exceptions.py
├── models/       9 modelos ORM (1 archivo/tabla) + mixins.py
├── schemas/      Pydantic: ingesta.py (validación nivel 1) · lectura.py · catalogos.py · riesgo.py
├── repositories/ BaseRepository[T] + 1 repo por entidad
├── services/     validacion_service · ingesta_service · riesgo/ · anomalias/
├── routers/      salud · ingesta · lecturas · catalogos · riesgo
├── simulacion/   SimuladorSensor (ABC) → MQ7 / HumedadSuelo · EscenarioRiesgo
└── main.py       crear_app()
migrations/  002_timescale.sql · 003_vistas.sql · 004_seed_catalogos.sql
scripts/     init_db.py · seed_historico.py · simulador.py
tests/       test_ingesta_schema · test_validacion · test_riesgo · test_anomalias
```
