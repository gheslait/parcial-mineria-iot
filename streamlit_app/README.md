# Fase 3 — Aplicación analítica en Streamlit

Un solo archivo `app.py` (estilo del ejemplo del profesor): script plano de
arriba a abajo, con **matplotlib + seaborn**. Se conecta **directo a
PostgreSQL / TimescaleDB** (sin cargar archivos a mano), igual que Power BI.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # DATABASE_URL + DB_SCHEMA (misma BD que la API)
```

Requiere que la base ya tenga datos:
`../api/scripts/init_db.py` y `../api/scripts/seed_historico.py --dias 20`.

## Ejecutar

```bash
streamlit run app.py            # http://localhost:8501
```

## Secciones de `app.py` (en orden)

1. **Título** y carga de datos desde PostgreSQL (`pd.read_sql` a `vw_lecturas_enriquecidas`).
2. **Vista previa** — `data.head()`, dimensiones.
3. **Estadísticas descriptivas** — `data.describe(include="all")`.
4. **Tablas dinámicas** — `pivot_table` con selección de variable para filas/columnas.
5. **Gráficos de distribución** — `sns.histplot` (numéricas) y conteo (categóricas).
6. **Matriz de correlación** — `sns.heatmap` de `data.corr()`.
7. **Limpieza básica** — nulos, duplicados, valores fuera de rango físico; opción de limpiar.
8. **Detección de valores atípicos** — z-score e IQR (umbrales ajustables) + gráfico.
9. **Filtros dinámicos** — `multiselect` de columnas + `slider` / `multiselect` por columna.
10. **Modelos de Machine Learning** — 2 algoritmos:
    - **Regresión** (`RandomForestRegressor`) → pronóstico del CO del siguiente instante. MAE, RMSE, R², gráfico real vs predicho, importancia de variables.
    - **Clasificación** (`RandomForestClassifier`) → nivel de riesgo de combustión (bajo/medio/alto/crítico). Accuracy, F1 macro, matriz de confusión, importancia de variables.
11. **Resumen final** — `st.metric` (filas, columnas, nulos, eventos de riesgo).

## Despliegue (opcional, como el ejemplo del profesor)

1. Subir `app.py` y `requirements.txt` a un repo de GitHub.
2. En [share.streamlit.io](https://share.streamlit.io) → *Deploy a public app from GitHub*.
3. En *Advanced settings* → *Secrets*, pegar:
   ```
   DATABASE_URL="postgresql+psycopg2://usuario:clave@gheslait.com:15432/timescaledb"
   DB_SCHEMA="combustion_riesgo"
   ```
