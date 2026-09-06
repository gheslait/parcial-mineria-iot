"""
`DetectorAtipicos` — identifica valores atípicos en Streamlit (Fase 3:
"identificar valores atípicos o anómalos").

Implementación en pandas/numpy, independiente de la API. Dos métodos clásicos:
z-score y rango intercuartílico (IQR / Tukey), aplicados por variable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class DetectorAtipicos:
    def __init__(self, z_umbral: float = 3.0, iqr_factor: float = 1.5) -> None:
        self.z_umbral = z_umbral
        self.iqr_factor = iqr_factor

    def _zscore(self, s: pd.Series) -> pd.Series:
        mu, sigma = s.mean(), s.std(ddof=1)
        if not sigma or np.isnan(sigma):
            return pd.Series(False, index=s.index)
        return ((s - mu) / sigma).abs() > self.z_umbral

    def _iqr(self, s: pd.Series) -> pd.Series:
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if not iqr or np.isnan(iqr):
            return pd.Series(False, index=s.index)
        return (s < q1 - self.iqr_factor * iqr) | (s > q3 + self.iqr_factor * iqr)

    def marcar(self, df_ancho: pd.DataFrame) -> pd.DataFrame:
        """Devuelve el df con columnas `<var>_atipico_z` y `<var>_atipico_iqr`."""
        out = df_ancho.copy()
        for col in df_ancho.columns:
            out[f"{col}_atipico_z"] = self._zscore(df_ancho[col])
            out[f"{col}_atipico_iqr"] = self._iqr(df_ancho[col])
        return out

    def tabla_atipicos(self, df_ancho: pd.DataFrame) -> pd.DataFrame:
        """Lista larga de los puntos marcados por cualquiera de los dos métodos."""
        filas = []
        for col in df_ancho.columns:
            z = self._zscore(df_ancho[col])
            q = self._iqr(df_ancho[col])
            marcado = z | q
            for ts, val in df_ancho.loc[marcado, col].items():
                filas.append(
                    {
                        "medido_en": ts,
                        "variable": col,
                        "valor": val,
                        "metodo": "z-score + IQR" if (z[ts] and q[ts]) else ("z-score" if z[ts] else "IQR"),
                    }
                )
        return pd.DataFrame(filas).sort_values("medido_en") if filas else pd.DataFrame()

    def resumen(self, df_ancho: pd.DataFrame) -> pd.DataFrame:
        filas = []
        for col in df_ancho.columns:
            z = int(self._zscore(df_ancho[col]).sum())
            q = int(self._iqr(df_ancho[col]).sum())
            filas.append(
                {
                    "variable": col,
                    "n": int(df_ancho[col].notna().sum()),
                    "atipicos_zscore": z,
                    "atipicos_iqr": q,
                    "%_zscore": round(100 * z / max(len(df_ancho), 1), 2),
                }
            )
        return pd.DataFrame(filas)
