"""
Genera histórico simulado y lo inserta DIRECTO en la base de datos (inserción
masiva con SQLAlchemy Core, rápida sobre conexión remota).

    python scripts/seed_historico.py --dias 20
    python scripts/seed_historico.py --dias 7 --intervalo-seg 30 --limpiar

Inserta en: lectura, anomalia, evento_riesgo, estado_dispositivo.
Reutiliza los detectores y el evaluador de riesgo reales (`app.services`).
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, insert, select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Anomalia,
    Dispositivo,
    EstadoDispositivo,
    EventoRiesgo,
    Lectura,
    ReglaRiesgo,
    Sensor,
    TipoSensor,
)
from app.services.anomalias import DETECTORES  # noqa: E402
from app.services.anomalias.base import Contexto  # noqa: E402
from app.services.riesgo import EvaluadorRiesgo  # noqa: E402
from app.simulacion import EscenarioRiesgo  # noqa: E402

_VENTANA = 60
_CHUNK = 10_000


def _insertar(db, tabla, filas: list[dict]) -> None:
    for i in range(0, len(filas), _CHUNK):
        db.execute(insert(tabla), filas[i : i + _CHUNK])
        db.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dias", type=int, default=20)
    ap.add_argument("--intervalo-seg", type=int, default=60)
    ap.add_argument("--codigo-dispositivo", default=get_settings().dispositivo_codigo)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--limpiar", action="store_true")
    args = ap.parse_args()

    escenario = EscenarioRiesgo(semilla=args.semilla)
    evaluador = EvaluadorRiesgo()
    t0 = time.monotonic()

    with SessionLocal() as db:
        disp = db.scalar(select(Dispositivo).where(Dispositivo.codigo == args.codigo_dispositivo))
        if disp is None:
            sys.exit(f"No existe el dispositivo {args.codigo_dispositivo!r}. Corre init_db.py primero.")

        if args.limpiar:
            sensores_ids = list(db.scalars(select(Sensor.id).where(Sensor.id_dispositivo == disp.id)))
            db.execute(delete(Anomalia).where(Anomalia.id_sensor.in_(sensores_ids)))
            db.execute(delete(EventoRiesgo).where(EventoRiesgo.id_dispositivo == disp.id))
            db.execute(delete(EstadoDispositivo).where(EstadoDispositivo.id_dispositivo == disp.id))
            db.execute(delete(Lectura).where(Lectura.id_dispositivo == disp.id))
            db.commit()
            print("  -> histórico anterior del dispositivo eliminado")

        tipos = {x.clave: x for x in db.scalars(select(TipoSensor))}
        sensores = {
            s.tipo_sensor.clave: s
            for s in db.scalars(select(Sensor).where(Sensor.id_dispositivo == disp.id))
        }
        reglas: list[ReglaRiesgo] = list(
            db.scalars(select(ReglaRiesgo).where(ReglaRiesgo.activo.is_(True)))
        )

        inicio = (datetime.now(timezone.utc) - timedelta(days=args.dias)).replace(
            second=0, microsecond=0
        )
        fin = datetime.now(timezone.utc)
        paso = timedelta(seconds=args.intervalo_seg)
        rmin = {k: float(v.rango_min) for k, v in tipos.items()}
        rmax = {k: float(v.rango_max) for k, v in tipos.items()}

        historicos: dict[str, list[float]] = {"MQ7": [], "HUM_SUELO": []}
        f_lect: list[dict] = []
        f_anom: list[dict] = []
        f_even: list[dict] = []
        f_est: list[dict] = []
        ultimo_evento_hora: datetime | None = None

        t = inicio
        while t < fin:
            valores: dict[str, float] = {}
            for sim in escenario.lecturas_en(t):
                if sim.valor is None:
                    continue
                clave = sim.clave
                calidad = "valida"

                ctx = Contexto(
                    clave_tipo=clave,
                    rango_min=rmin[clave],
                    rango_max=rmax[clave],
                    historico=historicos[clave][-_VENTANA:],
                )
                marcada = False
                for det in DETECTORES:
                    h = det.detectar(sim.valor, ctx)
                    if h is None:
                        continue
                    marcada = True
                    f_anom.append(
                        dict(
                            id_sensor=sensores[clave].id,
                            lectura_medido_en=t,
                            metodo=h.metodo,
                            valor=h.valor,
                            score=h.score,
                            descripcion=h.descripcion,
                            detectado_en=t,
                        )
                    )
                if marcada:
                    calidad = "sospechosa"
                # El histórico sigue al proceso real: se alimenta con el valor
                # simulado salvo cuando la lectura fue corrupta a propósito.
                if sim.anomalia_forzada is None:
                    historicos[clave].append(sim.valor)

                f_lect.append(
                    dict(
                        medido_en=t,
                        id_sensor=sensores[clave].id,
                        id_dispositivo=disp.id,
                        valor=round(sim.valor, 4),
                        unidad=sim.unidad,
                        crudo=sim.crudo,
                        calidad=calidad,
                        recibido_en=t,
                    )
                )
                valores[clave] = sim.valor

            hora_actual = t.replace(minute=0, second=0, microsecond=0)
            if valores and hora_actual != ultimo_evento_hora:
                tend = 0.0
                if len(historicos["MQ7"]) >= 10:
                    tend = (historicos["MQ7"][-1] - historicos["MQ7"][-10]) / (
                        9 * args.intervalo_seg / 60
                    )
                res = evaluador.evaluar(
                    co_ppm=valores.get("MQ7"),
                    humedad_pct=valores.get("HUM_SUELO"),
                    tendencia_co_ppm_min=tend,
                    reglas=reglas,
                    valores_por_clave=valores,
                )
                if res.amerita_evento:
                    f_even.append(
                        dict(
                            id_dispositivo=disp.id,
                            id_regla=res.id_regla,
                            nivel=res.nivel,
                            score=res.score,
                            valor_mq7=res.valor_mq7,
                            valor_humedad=res.valor_humedad,
                            mensaje=res.mensaje,
                            estado="abierto",
                            detectado_en=t,
                        )
                    )
                    ultimo_evento_hora = hora_actual

            if t.minute % 10 == 0 and t.second == 0:
                f_est.append(
                    dict(
                        id_dispositivo=disp.id,
                        wifi_rssi=-55 - (t.minute % 20),
                        memoria_libre=90000 + t.minute * 7,
                        uptime_seg=int((t - inicio).total_seconds()),
                        envio_ok=True,
                        mensaje_lcd=f"CO {valores.get('MQ7', 0):.0f} H {valores.get('HUM_SUELO', 0):.0f}%",
                        reportado_en=t,
                    )
                )
            t += paso

        print(
            f"Generado en {time.monotonic() - t0:.1f}s  "
            f"lecturas={len(f_lect)} anomalias={len(f_anom)} "
            f"eventos={len(f_even)} heartbeats={len(f_est)}"
        )
        print("Insertando (bulk)...")
        _insertar(db, Lectura.__table__, f_lect)
        _insertar(db, Anomalia.__table__, f_anom)
        _insertar(db, EventoRiesgo.__table__, f_even)
        _insertar(db, EstadoDispositivo.__table__, f_est)

    _refrescar_agregado()
    print(f"OK en {time.monotonic() - t0:.1f}s total")


def _refrescar_agregado() -> None:
    """El agregado continuo se materializa fuera de transacción."""
    from sqlalchemy.engine import make_url

    import psycopg2

    url = make_url(get_settings().database_url)
    conn = psycopg2.connect(
        host=url.host, port=url.port, dbname=url.database,
        user=url.username, password=url.password,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{get_settings().db_schema_seguro}", public')
        cur.execute("CALL refresh_continuous_aggregate('ca_lecturas_15min', NULL, NULL)")
    conn.close()
    print("  -> ca_lecturas_15min refrescado")


if __name__ == "__main__":
    main()
