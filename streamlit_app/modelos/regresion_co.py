"""
Modelo 1 (regresión): pronostica el nivel de CO (MQ7) del siguiente instante.

Algoritmo: RandomForestRegressor. Variable objetivo: CO desplazado -1 paso.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from modelos.base import ModeloPrediccion, ResultadoEntrenamiento
from modelos.features import features_temporales, particion_temporal


class RegresorCO(ModeloPrediccion):
    nombre = "Pronóstico de CO (RandomForestRegressor)"
    tipo = "regresion"

    def __init__(self, n_estimators: int = 200, max_depth: int | None = 12, **kw) -> None:
        super().__init__(n_estimators=n_estimators, max_depth=max_depth, **kw)
        self._modelo = RandomForestRegressor(
            n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
        )

    def construir_features(self, df_ancho: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        X = features_temporales(df_ancho)
        y = df_ancho["MQ7"].shift(-1).rename("MQ7_siguiente")  # horizonte: +1 paso
        datos = X.join(y).dropna()
        return datos.drop(columns="MQ7_siguiente"), datos["MQ7_siguiente"]

    def entrenar(self, df_ancho: pd.DataFrame) -> ResultadoEntrenamiento:
        X, y = self.construir_features(df_ancho)
        X_tr, X_te, y_tr, y_te = particion_temporal(X, y)
        self._modelo.fit(X_tr, y_tr)
        y_pred = pd.Series(self._modelo.predict(X_te), index=y_te.index, name="pred")

        self._entrenado = True
        self.resultado = ResultadoEntrenamiento(
            metricas={
                "MAE": mean_absolute_error(y_te, y_pred),
                "RMSE": float(np.sqrt(mean_squared_error(y_te, y_pred))),
                "R2": r2_score(y_te, y_pred),
                "n_entrenamiento": len(X_tr),
                "n_prueba": len(X_te),
            },
            y_test=y_te,
            y_pred=y_pred,
            importancias=pd.Series(self._modelo.feature_importances_, index=X.columns)
            .sort_values(ascending=False),
        )
        return self.resultado

    def predecir(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self._modelo.predict(X), index=X.index, name="MQ7_pred")
