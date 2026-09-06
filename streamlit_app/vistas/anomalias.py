"""Vista 3 — Valores atípicos: detección en Streamlit + anomalías registradas por la API."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dominio.anomalias import DetectorAtipicos
from vistas.comun import contexto, repo


def render() -> None:
    st.title("Valores atípicos y anómalos")
    filtros, largo, ancho = contexto()
    if ancho.empty:
        st.warning("No hay datos para analizar.")
        return

    c1, c2 = st.columns(2)
    z = c1.slider("Umbral z-score", 2.0, 5.0, 3.0, 0.1)
    k = c2.slider("Factor IQR", 1.0, 3.0, 1.5, 0.1)
    detector = DetectorAtipicos(z_umbral=z, iqr_factor=k)

    st.subheader("Resumen de detección (este subconjunto)")
    st.dataframe(detector.resumen(ancho), use_container_width=True)

    st.subheader("Puntos marcados sobre la serie")
    marcado = detector.marcar(ancho)
    for var in ancho.columns:
        fig = go.Figure()
        fig.add_scatter(x=ancho.index, y=ancho[var], mode="lines", name=var, line=dict(color="#888"))
        at = marcado[marcado[f"{var}_atipico_z"] | marcado[f"{var}_atipico_iqr"]]
        fig.add_scatter(
            x=at.index, y=at[var], mode="markers", name="atípico",
            marker=dict(color="#c62828", size=7, symbol="x"),
        )
        fig.update_layout(height=300, title=var, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    tabla = detector.tabla_atipicos(ancho)
    if not tabla.empty:
        st.dataframe(tabla, use_container_width=True, height=260)

    st.divider()
    st.subheader("Anomalías registradas por la API (tabla `anomalia`)")
    api_an = repo().anomalias(filtros.ts_desde, filtros.ts_hasta)
    if api_an.empty:
        st.info("Sin anomalías registradas por la API en este rango.")
    else:
        m1, m2 = st.columns(2)
        m1.metric("Total", len(api_an))
        m2.metric("Métodos", ", ".join(sorted(api_an["metodo"].unique())))
        st.plotly_chart(
            px.scatter(
                api_an, x="detectado_en", y="valor", color="metodo", symbol="tipo_sensor",
                hover_data=["descripcion"], title="Anomalías detectadas por la API",
            ),
            use_container_width=True,
        )
        st.dataframe(api_an, use_container_width=True, height=260)
