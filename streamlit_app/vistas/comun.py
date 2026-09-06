"""Elementos compartidos por las vistas: repositorio, barra de filtros, carga de datos."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from core.db import RepositorioLecturas
from dominio.filtros import Filtros

PALETA = {"MQ7": "#e4572e", "HUM_SUELO": "#3d7dca"}
NIVEL_COLOR = {"bajo": "#2e7d32", "medio": "#f9a825", "alto": "#ef6c00", "critico": "#c62828"}


@st.cache_resource
def repo() -> RepositorioLecturas:
    return RepositorioLecturas()


def barra_lateral_filtros() -> Filtros:
    """Filtros dinámicos (fecha, variable, rango de valores, dispositivo, calidad)."""
    r = repo()
    lo, hi = r.rango_fechas()
    if lo is None:
        st.sidebar.error("No hay lecturas en la base de datos. Corre `seed_historico.py`.")
        st.stop()
    lo, hi = pd.Timestamp(lo).date(), pd.Timestamp(hi).date()

    st.sidebar.header("Filtros")
    defecto_desde = max(lo, hi - timedelta(days=7))
    rango = st.sidebar.date_input(
        "Rango de fechas", value=(defecto_desde, hi), min_value=lo, max_value=hi
    )
    desde, hasta = rango if isinstance(rango, tuple) and len(rango) == 2 else (defecto_desde, hi)

    tipos_disp = r.tipos_sensor()
    tipos = st.sidebar.multiselect("Variables", tipos_disp, default=tipos_disp)

    dispositivos = r.dispositivos()
    disp = st.sidebar.selectbox("Dispositivo", ["(todos)"] + dispositivos)
    disp = None if disp == "(todos)" else disp

    usar_rango = st.sidebar.checkbox("Filtrar por rango de valores")
    vmin = vmax = None
    if usar_rango:
        vmin, vmax = st.sidebar.slider(
            "Valor (aplica a la variable seleccionada)", -50.0, 1000.0, (0.0, 1000.0)
        )

    calidad = st.sidebar.selectbox("Calidad", ["(todas)", "valida", "sospechosa", "invalida"])

    return Filtros(
        desde=desde, hasta=hasta, tipos=tuple(tipos), dispositivo=disp,
        valor_min=vmin, valor_max=vmax, calidad=calidad,
    )


@st.cache_data(ttl=300, show_spinner="Cargando lecturas...")
def cargar_largo(clave: tuple) -> pd.DataFrame:
    f: Filtros = st.session_state["_filtros"]
    return repo().lecturas(
        f.ts_desde, f.ts_hasta, tipos=f.tipos or None, dispositivo=f.dispositivo,
        valor_min=f.valor_min, valor_max=f.valor_max, calidad=f.calidad,
    )


@st.cache_data(ttl=300, show_spinner="Preparando serie...")
def cargar_ancho(clave: tuple) -> pd.DataFrame:
    f: Filtros = st.session_state["_filtros"]
    return repo().pivote(f.ts_desde, f.ts_hasta, dispositivo=f.dispositivo)


def contexto():
    """Guarda los filtros en session_state y devuelve (filtros, df_largo, df_ancho)."""
    f = barra_lateral_filtros()
    st.session_state["_filtros"] = f
    return f, cargar_largo(f.clave_cache()), cargar_ancho(f.clave_cache())
