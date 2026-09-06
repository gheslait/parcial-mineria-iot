"""
Inicializa la base de datos del proyecto (idempotente).

    python scripts/init_db.py            # crea/actualiza todo
    python scripts/init_db.py --reset    # BORRA el schema del grupo y lo recrea

Pasos:
  1. CREATE SCHEMA <DB_SCHEMA>
  2. Base.metadata.create_all  -> las 9 tablas ORM
  3. migrations/002_timescale.sql  -> hypertable + agregado continuo   (autocommit)
  4. migrations/003_vistas.sql     -> vistas para Streamlit / Power BI
  5. migrations/004_seed_catalogos.sql -> tipo_sensor + regla_riesgo
  6. seed de grupo / dispositivo / sensores desde api/.env (identidad del despliegue)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2
from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings          # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Dispositivo, Grupo, Sensor, TipoSensor  # noqa: E402

MIGRACIONES = ["002_timescale.sql", "003_vistas.sql", "004_seed_catalogos.sql"]
_DIR_MIGRACIONES = Path(__file__).resolve().parents[1] / "migrations"


def _conn_autocommit(schema: str) -> psycopg2.extensions.connection:
    url = make_url(get_settings().database_url)
    conn = psycopg2.connect(
        host=url.host,
        port=url.port,
        dbname=url.database,
        user=url.username,
        password=url.password,
        connect_timeout=15,
    )
    conn.autocommit = True   # DDL de TimescaleDB (CAgg, políticas) no admite transacción
    with conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public')
    return conn


def _aplicar_sql(conn, archivo: str) -> None:
    ruta = _DIR_MIGRACIONES / archivo
    print(f"  -> {archivo}")
    with conn.cursor() as cur:
        cur.execute(ruta.read_text(encoding="utf-8"))


def _seed_identidad() -> None:
    s = get_settings()
    with SessionLocal() as db, db.begin():
        grupo = db.query(Grupo).filter_by(numero=s.grupo_numero).one_or_none()
        if grupo is None:
            grupo = Grupo(nombre=s.grupo_nombre, numero=s.grupo_numero)
            db.add(grupo)
            db.flush()

        disp = db.query(Dispositivo).filter_by(codigo=s.dispositivo_codigo).one_or_none()
        if disp is None:
            disp = Dispositivo(
                id_grupo=grupo.id,
                codigo=s.dispositivo_codigo,
                descripcion="ESP32 + MQ7 + humedad de suelo (monitoreo de combustion)",
                ubicacion="Laboratorio",
            )
            db.add(disp)
            db.flush()

        for clave in ("MQ7", "HUM_SUELO"):
            tipo = db.query(TipoSensor).filter_by(clave=clave).one()
            existe = (
                db.query(Sensor)
                .filter_by(id_dispositivo=disp.id, id_tipo_sensor=tipo.id)
                .one_or_none()
            )
            if existe is None:
                db.add(
                    Sensor(
                        id_dispositivo=disp.id,
                        id_tipo_sensor=tipo.id,
                        etiqueta=f"{clave} {disp.codigo}",
                        pin={"MQ7": "GPIO34", "HUM_SUELO": "GPIO35"}[clave],
                    )
                )
        print(f"  -> grupo #{grupo.numero!r}, dispositivo {disp.codigo!r}, 2 sensores")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="DROP SCHEMA CASCADE antes de crear")
    args = parser.parse_args()

    schema = get_settings().db_schema_seguro
    print(f"Base de datos: {make_url(get_settings().database_url).render_as_string(hide_password=True)}")
    print(f"Schema       : {schema}")

    conn = _conn_autocommit("public")
    with conn.cursor() as cur:
        if args.reset:
            print(f"  -> DROP SCHEMA {schema} CASCADE")
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    conn.close()

    print("Creando tablas ORM (create_all)...")
    Base.metadata.create_all(engine)

    print("Aplicando migraciones SQL...")
    conn = _conn_autocommit(schema)
    for archivo in MIGRACIONES:
        _aplicar_sql(conn, archivo)
    conn.close()

    print("Sembrando identidad del grupo/dispositivo...")
    _seed_identidad()

    # Resumen
    conn = _conn_autocommit(schema)
    with conn.cursor() as cur:
        cur.execute(
            "select table_name from information_schema.tables "
            "where table_schema = %s and table_type = 'BASE TABLE' order by 1",
            (schema,),
        )
        tablas = [r[0] for r in cur.fetchall()]
        cur.execute(
            "select hypertable_name from timescaledb_information.hypertables "
            "where hypertable_schema = %s",
            (schema,),
        )
        hyper = [r[0] for r in cur.fetchall()]
    conn.close()

    print(f"\nOK. {len(tablas)} tablas: {', '.join(tablas)}")
    print(f"Hypertables: {', '.join(hyper) or '(ninguna)'}")


if __name__ == "__main__":
    main()
