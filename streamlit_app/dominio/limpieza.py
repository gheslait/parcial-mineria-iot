"""
`LimpiadorDatos` — limpieza básica (Fase 3: "limpieza básica").

Opera sobre el DataFrame ancho (índice temporal, columnas = variables) y deja
registro de cuánto quitó/ajustó cada paso para mostrarlo en la vista.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class LimpiadorDatos:
    rangos_fisicos: dict[str, tuple[float, float]]
    bitacora: dict[str, int] = field(default_factory=dict)

    def limpiar(
        self,
        df: pd.DataFrame,
        *,
        quitar_duplicados: bool = True,
        recortar_fisico: bool = True,
        interpolar: bool = True,
        resamplear: str | None = None,
    ) -> pd.DataFrame:
        self.bitacora = {}
        out = df.copy()

        if quitar_duplicados:
            antes = len(out)
            out = out[~out.index.duplicated(keep="first")]
            self.bitacora["duplicados_por_timestamp"] = antes - len(out)

        if recortar_fisico:
            fuera = 0
            for col in out.columns:
                lo, hi = self.rangos_fisicos.get(col, (None, None))
                if lo is None:
                    continue
                mask = (out[col] < lo) | (out[col] > hi)
                fuera += int(mask.sum())
                out.loc[mask, col] = pd.NA
            self.bitacora["valores_fuera_de_rango_fisico"] = fuera

        self.bitacora["nulos_iniciales"] = int(out.isna().sum().sum())

        if resamplear:
            out = out.resample(resamplear).mean()
            self.bitacora["filas_tras_resampleo"] = len(out)

        if interpolar:
            nulos_antes = int(out.isna().sum().sum())
            out = out.interpolate(method="time", limit=6).ffill().bfill()
            self.bitacora["nulos_interpolados"] = nulos_antes - int(out.isna().sum().sum())

        self.bitacora["filas_finales"] = len(out)
        return out
