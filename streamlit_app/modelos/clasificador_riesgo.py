"""
Modelo 2 (clasificación): predice el nivel de riesgo de combustión
(bajo / medio / alto / critico) del siguiente instante.

Algoritmo: RandomForestClassifier. La etiqueta se deriva del índice de riesgo
(`dominio.etiquetas`), consistente con la lógica de la API.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
)

from dominio.etiquetas import NIVELES, etiquetar_riesgo
from modelos.base import ModeloPrediccion, ResultadoEntrenamiento
from modelos.features import features_temporales, particion_temporal


class ClasificadorRiesgo(ModeloPrediccion):
    nombre = "Nivel de riesgo (RandomForestClassifier)"
    tipo = "clasificacion"

    def __init__(self, n_estimators: int = 250, max_depth: int | None = 14, **kw) -> None:
        super().__init__(n_estimators=n_estimators, max_depth=max_depth, **kw)
        self._modelo = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )

    def construir_features(self, df_ancho: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        X = features_temporales(df_ancho)
        y = etiquetar_riesgo(df_ancho).shift(-1)  # nivel del siguiente instante
        datos = X.join(y).dropna()
        return datos.drop(columns="riesgo_nivel"), datos["riesgo_nivel"]

    def entrenar(self, df_ancho: pd.DataFrame) -> ResultadoEntrenamiento:
        X, y = self.construir_features(df_ancho)
        X_tr, X_te, y_tr, y_te = particion_temporal(X, y)
        self._modelo.fit(X_tr, y_tr)
        y_pred = pd.Series(self._modelo.predict(X_te), index=y_te.index, name="pred")

        etiquetas = [n for n in NIVELES if n in set(y_te) | set(y_pred)]
        cm = confusion_matrix(y_te, y_pred, labels=etiquetas)

        self._entrenado = True
        self.resultado = ResultadoEntrenamiento(
            metricas={
                "accuracy": accuracy_score(y_te, y_pred),
                "balanced_accuracy": balanced_accuracy_score(y_te, y_pred),
                "f1_macro": f1_score(y_te, y_pred, average="macro"),
                "n_entrenamiento": len(X_tr),
                "n_prueba": len(X_te),
            },
            y_test=y_te,
            y_pred=y_pred,
            importancias=pd.Series(self._modelo.feature_importances_, index=X.columns)
            .sort_values(ascending=False),
            extra={"matriz_confusion": pd.DataFrame(cm, index=etiquetas, columns=etiquetas)},
        )
        return self.resultado

    def predecir(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self._modelo.predict(X), index=X.index, name="riesgo_pred")
