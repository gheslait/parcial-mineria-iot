"""
Simulador del ESP32: arma el payload JSON y lo envía por HTTP POST a la API,
igual que hará el firmware real.

    python scripts/simulador.py --http --intervalo 5
    python scripts/simulador.py --http --intervalo 5 --n 100 --acelerar 60

Opciones:
    --intervalo   segundos entre envíos (tiempo real de pared)
    --acelerar    factor de tiempo simulado por envío (60 = cada envío avanza 1 min)
    --n           número de envíos (por defecto: infinito)
    --url         endpoint de ingesta
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.simulacion import EscenarioRiesgo  # noqa: E402


def _payload(escenario: EscenarioRiesgo, t: datetime, codigo: str) -> dict:
    lecturas = []
    for sim in escenario.lecturas_en(t):
        if sim.valor is None:  # dropout
            continue
        lecturas.append(
            {
                "tipo_sensor": sim.clave,
                "valor": sim.valor,
                "unidad": sim.unidad,
                "crudo": sim.crudo,
                "medido_en": t.isoformat(),
            }
        )
    co = next((x["valor"] for x in lecturas if x["tipo_sensor"] == "MQ7"), 0)
    hum = next((x["valor"] for x in lecturas if x["tipo_sensor"] == "HUM_SUELO"), 0)
    return {
        "codigo_dispositivo": codigo,
        "enviado_en": t.isoformat(),
        "lecturas": lecturas,
        "estado": {
            "wifi_rssi": -58,
            "memoria_libre": 91000,
            "uptime_seg": int(time.monotonic()),
            "envio_ok": True,
            "mensaje_lcd": f"CO {co:.0f}ppm H {hum:.0f}%",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--http", action="store_true", help="enviar a la API (si no, solo imprime)")
    ap.add_argument("--intervalo", type=float, default=5.0)
    ap.add_argument("--acelerar", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=0, help="0 = infinito")
    ap.add_argument(
        "--url", default="http://localhost:8000/api/v1/ingesta"
    )
    ap.add_argument("--codigo-dispositivo", default=get_settings().dispositivo_codigo)
    args = ap.parse_args()

    escenario = EscenarioRiesgo(semilla=int(time.time()) % 10_000)
    t = datetime.now(timezone.utc)
    enviados = 0
    cliente = httpx.Client(timeout=10.0) if args.http else None

    print(f"Simulador ESP32 -> {args.url if args.http else '(modo impresión)'}")
    try:
        while args.n == 0 or enviados < args.n:
            cuerpo = _payload(escenario, t, args.codigo_dispositivo)
            if cliente is not None:
                try:
                    r = cliente.post(args.url, json=cuerpo)
                    resumen = r.json()
                    ev = resumen.get("evento_riesgo")
                    print(
                        f"[{t:%Y-%m-%d %H:%M:%S}] {r.status_code} "
                        f"almacenadas={resumen.get('almacenadas')} "
                        f"anomalias={resumen.get('anomalias_detectadas')} "
                        + (f"RIESGO={ev['nivel']}({ev['score']})" if ev else "")
                    )
                except httpx.HTTPError as e:
                    print(f"[{t:%H:%M:%S}] error de red: {e}")
            else:
                print(cuerpo)

            enviados += 1
            t += timedelta(seconds=args.intervalo * args.acelerar)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print(f"\nDetenido. Envíos: {enviados}")
    finally:
        if cliente is not None:
            cliente.close()


if __name__ == "__main__":
    main()
