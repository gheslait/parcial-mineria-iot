"""
Aplicación analítica — Fase 3 del parcial integrador de Minería de Datos.

Sistema de monitoreo de riesgo de combustión (MQ7 + humedad de suelo).
Se conecta directo a PostgreSQL / TimescaleDB (solo lectura).

    streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="Riesgo de combustión — Analítica IoT",
    page_icon="🔥",
    layout="wide",
)

from vistas import anomalias, eda, exploracion, prediccion  # noqa: E402

PAGINAS = [
    st.Page(exploracion.render, title="Exploración", icon="📈", default=True),
    st.Page(eda.render, title="EDA y correlación", icon="🔎", url_path="eda"),
    st.Page(anomalias.render, title="Valores atípicos", icon="⚠️", url_path="anomalias"),
    st.Page(prediccion.render, title="Predicción (ML)", icon="🤖", url_path="prediccion"),
]

st.navigation(PAGINAS).run()
