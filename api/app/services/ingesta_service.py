"""
`IngestaService` — caso de uso central de la Fase 2.

Orquesta (composición de servicios y repositorios), sin SQL ni HTTP propios:

    1. resuelve el dispositivo por su código
    2. valida cada lectura (tipo/formato ya vino de Pydantic; aquí: rango físico)
    3. resuelve/crea el sensor y guarda la `lectura`
    4. pasa la lectura por los detectores de anomalías y las persiste
    5. evalúa el riesgo de combustión (índice + reglas) y crea `evento_riesgo`
    6. guarda el `estado_dispositivo` (heartbeat) si vino en el payload
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNoEncontrado
from app.models.anomalia import Anomalia
from app.models.estado_dispositivo import EstadoDispositivo
from app.models.evento_riesgo import EventoRiesgo
from app.models.lectura import Lectura
from app.repositories import (
    AnomaliaRepository,
    DispositivoRepository,
    EstadoDispositivoRepository,
    EventoRiesgoRepository,
    LecturaRepository,
    ReglaRiesgoRepository,
    SensorRepository,
    TipoSensorRepository,
)
from app.schemas.ingesta import PayloadESP32, RespuestaIngesta, ResultadoLectura
from app.services.anomalias import DETECTORES
from app.services.anomalias.base import Contexto
from app.services.riesgo import EvaluadorRiesgo
from app.services.validacion_service import ValidacionService

_VENTANA_HISTORICO = 60          # muestras previas para z-score / IQR / tendencia
_MUESTRAS_TENDENCIA = 10


class IngestaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dispositivos = DispositivoRepository(db)
        self.tipos = TipoSensorRepository(db)
        self.sensores = SensorRepository(db)
        self.lecturas = LecturaRepository(db)
        self.reglas = ReglaRiesgoRepository(db)
        self.eventos = EventoRiesgoRepository(db)
        self.anomalias = AnomaliaRepository(db)
        self.estados = EstadoDispositivoRepository(db)
        self.validacion = ValidacionService()
        self.evaluador = EvaluadorRiesgo()

    # ------------------------------------------------------------------
    def procesar(self, payload: PayloadESP32) -> RespuestaIngesta:
        dispositivo = self.dispositivos.obtener_por_codigo(payload.codigo_dispositivo)
        if dispositivo is None:
            raise RecursoNoEncontrado("dispositivo", payload.codigo_dispositivo)

        catalogo = self.tipos.mapa_por_clave()
        resultados: list[ResultadoLectura] = []
        valores_actuales: dict[str, float] = {}
        total_anomalias = 0

        for entrada in payload.lecturas:
            validada = self.validacion.validar(entrada, catalogo)
            sensor = self.sensores.obtener_o_crear(
                dispositivo.id,
                validada.tipo_sensor.id,
                etiqueta=f"{validada.tipo_sensor.clave} {dispositivo.codigo}",
            )
            medido_en = self._normalizar_tiempo(entrada.medido_en or payload.enviado_en)

            historico_prev = [
                float(x.valor)
                for x in self.lecturas.ultimas_por_sensor(sensor.id, _VENTANA_HISTORICO)
            ]

            lectura = self.lecturas.crear(
                Lectura(
                    medido_en=medido_en,
                    id_sensor=sensor.id,
                    id_dispositivo=dispositivo.id,
                    valor=validada.valor,
                    unidad=validada.unidad,
                    crudo=validada.crudo,
                    calidad=validada.calidad,
                )
            )
            valores_actuales[validada.tipo_sensor.clave] = validada.valor

            anomalias = self._detectar_anomalias(
                lectura, validada.tipo_sensor, historico_prev
            )
            total_anomalias += len(anomalias)
            if anomalias and lectura.calidad == "valida":
                lectura.calidad = "sospechosa"

            resultados.append(
                ResultadoLectura(
                    tipo_sensor=validada.tipo_sensor.clave,
                    valor=validada.valor,
                    calidad=lectura.calidad,
                    id_lectura=lectura.id,
                )
            )

        evento = self._evaluar_riesgo(dispositivo.id, valores_actuales)
        if payload.estado is not None:
            self._guardar_estado(dispositivo.id, payload.estado)

        return RespuestaIngesta(
            dispositivo=dispositivo.codigo,
            recibidas=len(payload.lecturas),
            almacenadas=len(resultados),
            resultados=resultados,
            anomalias_detectadas=total_anomalias,
            evento_riesgo=(
                {"nivel": evento.nivel, "score": float(evento.score), "mensaje": evento.mensaje}
                if evento is not None
                else None
            ),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _normalizar_tiempo(dt: datetime) -> datetime:
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    def _detectar_anomalias(
        self, lectura: Lectura, tipo, historico_prev: list[float]
    ) -> list[Anomalia]:
        ctx = Contexto(
            clave_tipo=tipo.clave,
            rango_min=float(tipo.rango_min),
            rango_max=float(tipo.rango_max),
            historico=historico_prev,
        )
        creadas: list[Anomalia] = []
        for detector in DETECTORES:
            hallazgo = detector.detectar(float(lectura.valor), ctx)
            if hallazgo is None:
                continue
            creadas.append(
                self.anomalias.crear(
                    Anomalia(
                        id_sensor=lectura.id_sensor,
                        id_lectura=lectura.id,
                        lectura_medido_en=lectura.medido_en,
                        metodo=hallazgo.metodo,
                        valor=hallazgo.valor,
                        score=hallazgo.score,
                        descripcion=hallazgo.descripcion,
                    )
                )
            )
        return creadas

    def _tendencia_co(self, id_dispositivo: int) -> float:
        """Pendiente reciente del CO en ppm/min (0 si no hay datos suficientes)."""
        sensor = self._sensor_de(id_dispositivo, "MQ7")
        if sensor is None:
            return 0.0
        recientes = self.lecturas.ultimas_por_sensor(sensor.id, _MUESTRAS_TENDENCIA)
        if len(recientes) < 3:
            return 0.0
        minutos = (recientes[-1].medido_en - recientes[0].medido_en).total_seconds() / 60.0
        if minutos <= 0:
            return 0.0
        return (float(recientes[-1].valor) - float(recientes[0].valor)) / minutos

    def _sensor_de(self, id_dispositivo: int, clave_tipo: str):
        tipo = self.tipos.obtener_por_clave(clave_tipo)
        if tipo is None:
            return None
        return self.sensores.resolver(id_dispositivo, tipo.id)

    def _evaluar_riesgo(
        self, id_dispositivo: int, valores_lote: dict[str, float]
    ) -> EventoRiesgo | None:
        co = valores_lote.get("MQ7") or self.lecturas.valor_mas_reciente(id_dispositivo, "MQ7")
        hum = valores_lote.get("HUM_SUELO") or self.lecturas.valor_mas_reciente(
            id_dispositivo, "HUM_SUELO"
        )
        if co is None and hum is None:
            return None

        resultado = self.evaluador.evaluar(
            co_ppm=co,
            humedad_pct=hum,
            tendencia_co_ppm_min=self._tendencia_co(id_dispositivo),
            reglas=self.reglas.activas(),
            valores_por_clave={**valores_lote},
        )
        if not resultado.amerita_evento:
            return None

        return self.eventos.crear(
            EventoRiesgo(
                id_dispositivo=id_dispositivo,
                id_regla=resultado.id_regla,
                nivel=resultado.nivel,
                score=resultado.score,
                valor_mq7=resultado.valor_mq7,
                valor_humedad=resultado.valor_humedad,
                mensaje=resultado.mensaje,
            )
        )

    def _guardar_estado(self, id_dispositivo: int, estado) -> None:
        self.estados.crear(
            EstadoDispositivo(
                id_dispositivo=id_dispositivo,
                wifi_rssi=estado.wifi_rssi,
                memoria_libre=estado.memoria_libre,
                uptime_seg=estado.uptime_seg,
                envio_ok=estado.envio_ok,
                mensaje_lcd=estado.mensaje_lcd,
            )
        )
