"""Vista 2 — EDA: distribución, calidad, correlación y estacionalidad."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from dominio.eda import AnalizadorEDA
from dominio.limpieza import LimpiadorDatos
from vistas.comun import contexto, repo


def render() -> None:
    st.title("Análisis exploratorio (EDA)")
    filtros, largo, ancho = contexto()
    if ancho.empty or ancho.shape[1] < 1:
        st.warning("No hay datos suficientes para el EDA.")
        return

    aplicar_limpieza = st.toggle("Aplicar limpieza básica antes de analizar", value=True)
    df = ancho
    if aplicar_limpieza:
        limpiador = LimpiadorDatos(rangos_fisicos=repo().rangos_fisicos())
        df = limpiador.limpiar(ancho, resamplear=None)
        with st.expander("Bitácora de limpieza"):
            st.json(limpiador.bitacora)

    eda = AnalizadorEDA(df)

    st.subheader("Resumen estadístico")
    st.dataframe(eda.resumen(), use_container_width=True)

    st.subheader("Distribución por variable")
    cols = st.columns(min(len(df.columns), 2))
    for i, var in enumerate(df.columns):
        with cols[i % len(cols)]:
            fig = px.histogram(df, x=var, nbins=50, marginal="box", title=var)
            fig.update_layout(height=300, margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Matriz de correlación")
    metodo = st.radio("Método", ["pearson", "spearman"], horizontal=True)
    corr = eda.matriz_correlacion(metodo)
    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto"
    )
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

    if {"MQ7", "HUM_SUELO"}.issubset(df.columns):
        st.caption("Correlación cruzada CO ↔ humedad para distintos desfases temporales:")
        cc = eda.correlacion_desfasada("MQ7", "HUM_SUELO", max_lag=30)
        st.plotly_chart(
            px.line(cc, x="lag", y="corr", title="Correlación desfasada (lag en pasos)"),
            use_container_width=True,
        )

    st.subheader("Estacionalidad diaria (media por hora)")
    perfil = eda.perfil_horario()
    st.plotly_chart(
        px.line(perfil, x=perfil.index, y=perfil.columns, labels={"x": "hora del día"}),
        use_container_width=True,
    )

    st.subheader("Datos faltantes por día (%)")
    st.dataframe(eda.faltantes_por_dia(), use_container_width=True)
