# Aplicación analítica — Fase 3

Streamlit + pandas + scikit-learn + plotly. Se conecta **directo a PostgreSQL /
TimescaleDB en modo lectura** (igual que Power BI).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # misma DATABASE_URL que la API (idealmente rol SELECT)
```

## Ejecutar

```bash
streamlit run app.py           # http://localhost:8501
```

Requiere que la base ya tenga datos: correr antes
`../api/scripts/init_db.py` y `../api/scripts/seed_historico.py --dias 20`.

## Páginas

| Página | Contenido |
|---|---|
| **Exploración** | series temporales interactivas, filtros dinámicos (fecha, variable, rango de valores, dispositivo, calidad), tabla y descarga CSV |
| **EDA y correlación** | resumen estadístico, distribución (histograma + boxplot), matriz de correlación (pearson/spearman), correlación cruzada CO↔humedad, estacionalidad horaria, faltantes por día, limpieza básica con bitácora |
| **Valores atípicos** | detección z-score + IQR (umbrales ajustables) sobre la serie, y las anomalías registradas por la API |
| **Predicción (ML)** | 2 modelos: `RegresorCO` (RandomForestRegressor) y `ClasificadorRiesgo` (RandomForestClassifier); métricas, importancia de variables, matriz de confusión y simulador interactivo del índice de riesgo |

## Estructura (POO)

```
core/      config.py · db.py (RepositorioLecturas)
dominio/   filtros.py · limpieza.py (LimpiadorDatos) · eda.py (AnalizadorEDA)
           anomalias.py (DetectorAtipicos) · etiquetas.py (índice de riesgo)
modelos/   base.py (ModeloPrediccion, ABC) · features.py
           regresion_co.py · clasificador_riesgo.py
vistas/    comun.py + exploracion / eda / anomalias / prediccion
app.py     navegación (st.navigation)
```
