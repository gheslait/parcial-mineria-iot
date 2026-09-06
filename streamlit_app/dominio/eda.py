"""`AnalizadorEDA` — estadística descriptiva y estructura de los datos."""
from __future__ import annotations

import numpy as np
import pandas as pd


class AnalizadorEDA:
    def __init__(self, df_ancho: pd.DataFrame) -> None:
        self.df = df_ancho

    def resumen(self) -> pd.DataFrame:
        d = self.df.describe().T
        d["faltantes"] = self.df.isna().sum()
        d["faltantes_%"] = (self.df.isna().mean() * 100).round(2)
        d["asimetria"] = self.df.skew(numeric_only=True)
        d["curtosis"] = self.df.kurtosis(numeric_only=True)
        return d.round(3)

    def faltantes_por_dia(self) -> pd.DataFrame:
        return self.df.isna().resample("1D").mean().mul(100).round(1)

    def matriz_correlacion(self, metodo: str = "pearson") -> pd.DataFrame:
        return self.df.corr(method=metodo, numeric_only=True)

    def perfil_horario(self) -> pd.DataFrame:
        """Media de cada variable por hora del día (estacionalidad diaria)."""
        g = self.df.copy()
        g["hora"] = g.index.hour
        return g.groupby("hora").mean(numeric_only=True)

    def correlacion_desfasada(self, a: str, b: str, max_lag: int = 30) -> pd.DataFrame:
        """Correlación cruzada entre dos variables para distintos desfases."""
        s_a, s_b = self.df[a], self.df[b]
        filas = []
        for k in range(-max_lag, max_lag + 1):
            filas.append({"lag": k, "corr": s_a.corr(s_b.shift(k))})
        return pd.DataFrame(filas)
