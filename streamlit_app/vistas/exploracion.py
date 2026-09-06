"""Vista 1 — Exploración: series temporales interactivas con filtros dinámicos."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from vistas.comun import PALETA, contexto


def render() -> None:
    st.title("Exploración de datos")
    st.caption(
        "Monitoreo de riesgo de combustión — MQ7 (monóxido de carbono) y humedad de suelo. "
        "Todos los filtros de la barra lateral son dinámicos."
    )

    filtros, largo, ancho = contexto()
    if largo.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lecturas", f"{len(largo):,}")
    c2.metric("Desde", str(filtros.desde))
    c3.metric("Hasta", str(filtros.hasta))
    c4.metric("Sospechosas", f"{(largo['calidad'] != 'valida').mean() * 100:.1f}%")

    st.subheader("Serie temporal")
    for tipo in filtros.tipos:
        sub = largo[largo["tipo_sensor"] == tipo]
        if sub.empty:
            continue
        fig = px.line(
            sub, x="medido_en", y="valor", color="calidad",
            title=f"{tipo} — {sub['magnitud'].iloc[0]} ({sub['unidad'].iloc[0]})",
            color_discrete_map={"valida": PALETA.get(tipo, "#555"), "sospechosa": "#f9a825", "invalida": "#c62828"},
        )
        fig.update_layout(height=320, legend_title=None, margin=dict(t=48, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Estadística descriptiva rápida"):
        st.dataframe(
            largo.groupby("tipo_sensor")["valor"].describe().round(2), use_container_width=True
        )

    st.subheader("Datos crudos")
    st.dataframe(largo.sort_values("medido_en", ascending=False), use_container_width=True, height=300)
    st.download_button(
        "Descargar CSV filtrado",
        largo.to_csv(index=False).encode("utf-8"),
        file_name="lecturas_filtradas.csv",
        mime="text/csv",
    )
