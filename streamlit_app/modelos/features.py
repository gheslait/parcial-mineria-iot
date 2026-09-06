"""Ingeniería de características compartida por los modelos."""
from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = (1, 2, 3, 6)
VENTANA_MOVIL = 6


def features_temporales(df_ancho: pd.DataFrame) -> pd.DataFrame:
    """Lags, medias móviles, tendencia y hora del día para MQ7 y HUM_SUELO."""
    x = pd.DataFrame(index=df_ancho.index)
    for col in ("MQ7", "HUM_SUELO"):
        if col not in df_ancho:
            continue
        s = df_ancho[col].astype(float)
        x[f"{col}"] = s
        for k in LAGS:
            x[f"{col}_lag{k}"] = s.shift(k)
        x[f"{col}_media{VENTANA_MOVIL}"] = s.rolling(VENTANA_MOVIL).mean()
        x[f"{col}_std{VENTANA_MOVIL}"] = s.rolling(VENTANA_MOVIL).std()
        x[f"{col}_tend"] = s.diff()
    hora = df_ancho.index.hour + df_ancho.index.minute / 60
    x["hora_sin"] = np.sin(2 * np.pi * hora / 24)
    x["hora_cos"] = np.cos(2 * np.pi * hora / 24)
    return x


def particion_temporal(X: pd.DataFrame, y: pd.Series, frac_test: float = 0.25):
    """Split respetando el orden del tiempo (sin fuga de datos)."""
    corte = int(len(X) * (1 - frac_test))
    return X.iloc[:corte], X.iloc[corte:], y.iloc[:corte], y.iloc[corte:]
