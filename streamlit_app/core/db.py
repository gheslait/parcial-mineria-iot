"""
`RepositorioLecturas` — único punto de acceso a PostgreSQL (solo lectura).

Streamlit se conecta directo a la BD (igual que Power BI). Todas las consultas
son parametrizadas y se cachean con `st.cache_data` (TTL 5 min).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from core.config import get_settings


@st.cache_resource
def _engine():
    s = get_settings()
    return create_engine(
        s.database_url,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={s.db_schema},public"},
    )


@st.cache_data(ttl=300, show_spinner=False)
def _leer(sql: str, params: dict | None = None) -> pd.DataFrame:
    with _engine().connect() as con:
        return pd.read_sql(text(sql), con, params=params or {})


class RepositorioLecturas:
    """Consultas de alto nivel que devuelven DataFrames listos para analizar."""

    # -- metadatos para poblar los filtros ------------------------------
    def rango_fechas(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        df = _leer("select min(medido_en) lo, max(medido_en) hi from lectura")
        return df.loc[0, "lo"], df.loc[0, "hi"]

    def dispositivos(self) -> list[str]:
        return _leer("select codigo from dispositivo order by codigo")["codigo"].tolist()

    def tipos_sensor(self) -> list[str]:
        return _leer("select clave from tipo_sensor order by clave")["clave"].tolist()

    def rangos_fisicos(self) -> dict[str, tuple[float, float]]:
        df = _leer("select clave, rango_min, rango_max from tipo_sensor")
        return {r.clave: (float(r.rango_min), float(r.rango_max)) for r in df.itertuples()}

    # -- datos -------------------------------------------------------
    def lecturas(
        self,
        desde,
        hasta,
        tipos: tuple[str, ...] | None = None,
        dispositivo: str | None = None,
        valor_min: float | None = None,
        valor_max: float | None = None,
        calidad: str | None = None,
        limite: int = 200_000,
    ) -> pd.DataFrame:
        sql = [
            "select medido_en, tipo_sensor, magnitud, valor, unidad, calidad,",
            "       dispositivo, id_sensor, hora_del_dia",
            "from vw_lecturas_enriquecidas where medido_en between :desde and :hasta",
        ]
        p: dict = {"desde": desde, "hasta": hasta, "limite": int(limite)}
        if tipos:
            sql.append("and tipo_sensor = any(:tipos)")
            p["tipos"] = list(tipos)
        if dispositivo:
            sql.append("and dispositivo = :disp")
            p["disp"] = dispositivo
        if valor_min is not None:
            sql.append("and valor >= :vmin")
            p["vmin"] = valor_min
        if valor_max is not None:
            sql.append("and valor <= :vmax")
            p["vmax"] = valor_max
        if calidad and calidad != "(todas)":
            sql.append("and calidad = :cal")
            p["cal"] = calidad
        sql.append("order by medido_en limit :limite")
        df = _leer(" ".join(sql), p)
        if not df.empty:
            df["medido_en"] = pd.to_datetime(df["medido_en"])
        return df

    def pivote(self, desde, hasta, dispositivo: str | None = None) -> pd.DataFrame:
        """Serie ancha: índice = tiempo, columnas = MQ7 / HUM_SUELO (valores válidos)."""
        df = self.lecturas(desde, hasta, dispositivo=dispositivo, calidad="valida")
        if df.empty:
            return df
        ancho = (
            df.pivot_table(index="medido_en", columns="tipo_sensor", values="valor", aggfunc="mean")
            .sort_index()
        )
        return ancho

    def anomalias(self, desde, hasta) -> pd.DataFrame:
        df = _leer(
            """
            select a.detectado_en, a.metodo, a.valor, a.score, a.descripcion,
                   ts.clave as tipo_sensor, d.codigo as dispositivo
            from anomalia a
            join sensor s on s.id = a.id_sensor
            join tipo_sensor ts on ts.id = s.id_tipo_sensor
            join dispositivo d on d.id = s.id_dispositivo
            where a.detectado_en between :desde and :hasta
            order by a.detectado_en
            """,
            {"desde": desde, "hasta": hasta},
        )
        if not df.empty:
            df["detectado_en"] = pd.to_datetime(df["detectado_en"])
        return df

    def eventos_riesgo(self, desde, hasta) -> pd.DataFrame:
        df = _leer(
            """
            select detectado_en, nivel, score, valor_mq7, valor_humedad, mensaje, estado
            from evento_riesgo
            where detectado_en between :desde and :hasta
            order by detectado_en
            """,
            {"desde": desde, "hasta": hasta},
        )
        if not df.empty:
            df["detectado_en"] = pd.to_datetime(df["detectado_en"])
        return df
