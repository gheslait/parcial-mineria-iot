"""
Índice y etiqueta de riesgo de combustión (réplica en pandas del `IndiceRiesgo`
de la API). Sirve para generar la variable objetivo del clasificador (Fase 3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_W_CO, _W_HUM, _W_TEND = 0.5, 0.35, 0.15
_CO_SEGURO, _CO_CRITICO = 9.0, 100.0
_HUM_CRITICA, _HUM_SEGURA = 12.0, 45.0
_TEND_CRITICA = 5.0
NIVELES = ["bajo", "medio", "alto", "critico"]


def _rampa(x, v0, v1):
    return np.clip((x - v0) / (v1 - v0) * 100.0, 0, 100)


def indice_riesgo(df: pd.DataFrame, col_co="MQ7", col_hum="HUM_SUELO") -> pd.Series:
    """Score 0–100 por fila. `df` debe tener índice temporal ordenado."""
    co = df[col_co].astype(float)
    hum = df[col_hum].astype(float)
    minutos = df.index.to_series().diff().dt.total_seconds().div(60).replace(0, np.nan)
    tendencia = co.diff().div(minutos).fillna(0).clip(lower=0)

    comp_co = _rampa(co, _CO_SEGURO, _CO_CRITICO)
    comp_hum = 100.0 - _rampa(hum, _HUM_CRITICA, _HUM_SEGURA)
    comp_tend = _rampa(tendencia, 0.0, _TEND_CRITICA)

    score = _W_CO * comp_co + _W_HUM * comp_hum + _W_TEND * comp_tend
    return pd.Series(np.clip(score, 0, 100), index=df.index, name="riesgo_score")


def etiquetar_riesgo(df: pd.DataFrame, **kw) -> pd.Series:
    score = indice_riesgo(df, **kw)
    cortes = [-0.1, 25, 50, 75, 100.1]
    return pd.cut(score, bins=cortes, labels=NIVELES).astype("object").rename("riesgo_nivel")
