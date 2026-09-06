"""Vista 4 — Predicción: entrena y evalúa los dos algoritmos de ML."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from dominio.etiquetas import indice_riesgo
from dominio.limpieza import LimpiadorDatos
from modelos import ClasificadorRiesgo, RegresorCO
from vistas.comun import contexto, repo


@st.cache_data(ttl=600, show_spinner="Entrenando modelos...")
def _entrenar(clave: tuple):
    f = st.session_state["_filtros"]
    ancho = repo().pivote(f.ts_desde, f.ts_hasta, dispositivo=f.dispositivo)
    if ancho.empty or not {"MQ7", "HUM_SUELO"}.issubset(ancho.columns):
        return None
    limpio = LimpiadorDatos(rangos_fisicos=repo().rangos_fisicos()).limpiar(
        ancho, resamplear="5min"
    )
    reg = RegresorCO()
    clf = ClasificadorRiesgo()
    r_reg = reg.entrenar(limpio)
    r_clf = clf.entrenar(limpio)
    return {"ancho": limpio, "reg": r_reg, "clf": r_clf}


def render() -> None:
    st.title("Predicción con Machine Learning")
    st.caption(
        "Dos algoritmos (Fase 3): **regresión** para pronosticar el CO y "
        "**clasificación** para el nivel de riesgo de combustión del siguiente instante. "
        "Partición temporal 75/25 sin fuga de datos."
    )
    filtros, largo, ancho = contexto()
    salida = _entrenar(filtros.clave_cache())
    if salida is None:
        st.warning("Se necesitan datos de MQ7 y humedad en el rango para entrenar. Amplía el rango de fechas.")
        return

    limpio, r_reg, r_clf = salida["ancho"], salida["reg"], salida["clf"]

    tab1, tab2 = st.tabs(["Regresión — CO", "Clasificación — riesgo"])

    with tab1:
        m = r_reg.metricas
        c1, c2, c3 = st.columns(3)
        c1.metric("MAE (ppm)", f"{m['MAE']:.2f}")
        c2.metric("RMSE (ppm)", f"{m['RMSE']:.2f}")
        c3.metric("R²", f"{m['R2']:.3f}")
        comp = pd.DataFrame({"real": r_reg.y_test, "prediccion": r_reg.y_pred})
        st.plotly_chart(
            px.line(comp, title="CO real vs. pronosticado (conjunto de prueba)"),
            use_container_width=True,
        )
        fig_disp = px.scatter(comp, x="real", y="prediccion", title="Dispersión real vs. predicho",
                              opacity=0.4)
        lim = [float(comp.min().min()), float(comp.max().max())]
        fig_disp.add_shape(type="line", x0=lim[0], y0=lim[0], x1=lim[1], y1=lim[1],
                           line=dict(dash="dash", color="#888"))
        st.plotly_chart(fig_disp, use_container_width=True)
        st.subheader("Importancia de variables")
        st.bar_chart(r_reg.importancias.head(12))

    with tab2:
        m = r_clf.metricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Accuracy", f"{m['accuracy']:.3f}")
        c2.metric("Balanced acc.", f"{m['balanced_accuracy']:.3f}")
        c3.metric("F1 macro", f"{m['f1_macro']:.3f}")
        cm = r_clf.extra["matriz_confusion"]
        st.plotly_chart(
            px.imshow(cm, text_auto=True, color_continuous_scale="Blues",
                      labels=dict(x="predicho", y="real"), title="Matriz de confusión"),
            use_container_width=True,
        )
        st.subheader("Importancia de variables")
        st.bar_chart(r_clf.importancias.head(12))
        dist = r_clf.y_test.value_counts().rename_axis("nivel").reset_index(name="n")
        st.plotly_chart(px.bar(dist, x="nivel", y="n", title="Distribución de clases (prueba)"),
                        use_container_width=True)

    st.divider()
    st.subheader("Simulador interactivo de riesgo")
    st.caption("Mueve los valores y observa el índice de riesgo de combustión (0–100).")
    s1, s2, s3 = st.columns(3)
    co = s1.slider("CO — MQ7 (ppm)", 0.0, 300.0, 15.0)
    hum = s2.slider("Humedad de suelo (%)", 0.0, 100.0, 30.0)
    tend = s3.slider("Tendencia de CO (ppm/min)", 0.0, 10.0, 0.0)
    df_pt = pd.DataFrame(
        {"MQ7": [co, co], "HUM_SUELO": [hum, hum]},
        index=pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:01"]),
    )
    df_pt.loc[df_pt.index[1], "MQ7"] = co + tend
    score = float(indice_riesgo(df_pt).iloc[1])
    nivel = pd.cut([score], [-0.1, 25, 50, 75, 100.1], labels=["bajo", "medio", "alto", "critico"])[0]
    st.metric("Índice de riesgo", f"{score:.0f}/100", nivel)
