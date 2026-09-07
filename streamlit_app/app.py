# ============================================================================
#  PARCIAL INTEGRADOR - MINERIA DE DATOS
#  Fase 3: Aplicacion analitica en Streamlit
#
#  Sistema de monitoreo de riesgo de combustion / incendio.
#  Sensores del grupo: MQ7 (monoxido de carbono, ppm) y humedad de suelo (%).
#
#
#  Ejecutar:  streamlit run app.py
# ============================================================================

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sqlalchemy import create_engine, text

load_dotenv()

st.set_page_config(page_title="Analisis Exploratorio - Riesgo de Combustion", layout="wide")
sns.set_style("whitegrid")


def config(clave, defecto=None):
    """Lee de variables de entorno (.env local) o de st.secrets (Streamlit Cloud)."""
    if clave in os.environ:
        return os.environ[clave]
    try:
        return st.secrets[clave]
    except Exception:
        return defecto

# ---------------------------------------------------------------------------
# Titulo principal
# ---------------------------------------------------------------------------
st.title("Analisis Exploratorio de Datos - Riesgo de Combustion")
st.write(
    "Datos de los sensores **MQ7** (monoxido de carbono) y **humedad de suelo**."
)

DATABASE_URL = config("DATABASE_URL")
DB_SCHEMA = config("DB_SCHEMA", "combustion_riesgo")


# ---------------------------------------------------------------------------
# Conexion y carga de datos desde PostgreSQL
# ---------------------------------------------------------------------------
@st.cache_resource
def obtener_engine():
    return create_engine(
        DATABASE_URL,
        connect_args={"options": f"-csearch_path={DB_SCHEMA},public"},
    )


@st.cache_data(ttl=300)
def cargar_datos():
    engine = obtener_engine()

    # Lecturas en formato largo (una fila por medicion)
    largo = pd.read_sql(
        text(
            "SELECT medido_en, tipo_sensor, valor, calidad, dispositivo "
            "FROM vw_lecturas_enriquecidas ORDER BY medido_en"
        ),
        engine,
    )
    largo["medido_en"] = pd.to_datetime(largo["medido_en"])

    # Pasar a formato ancho y agregar a intervalos de 5 minutos
    largo["bucket"] = largo["medido_en"].dt.floor("5min")
    ancho = largo.pivot_table(
        index="bucket", columns="tipo_sensor", values="valor", aggfunc="mean"
    ).rename(columns={"MQ7": "CO_ppm", "HUM_SUELO": "Humedad_suelo"})

    # Calidad del intervalo = la peor de las lecturas
    orden = {"valida": 0, "sospechosa": 1, "invalida": 2}
    inv = {v: k for k, v in orden.items()}
    calidad = (
        largo.assign(r=largo["calidad"].map(orden))
        .groupby("bucket")["r"]
        .max()
        .map(inv)
    )
    dispositivo = largo.groupby("bucket")["dispositivo"].first()

    df = ancho.copy()
    df["Calidad"] = calidad
    df["Dispositivo"] = dispositivo
    df = df.reset_index().rename(columns={"bucket": "Fecha_hora"})
    df["Fecha_hora"] = df["Fecha_hora"].dt.tz_localize(None)  # evita problemas de zona horaria
    df["Fecha"] = df["Fecha_hora"].dt.date.astype(str)
    df["Hora"] = df["Fecha_hora"].dt.hour
    df["Franja"] = pd.cut(
        df["Hora"], [-1, 5, 11, 17, 23],
        labels=["Madrugada", "Manana", "Tarde", "Noche"],
    ).astype(str)
    return df


@st.cache_data(ttl=300)
def contar_eventos_riesgo():
    engine = obtener_engine()
    return pd.read_sql(
        text("SELECT nivel, COUNT(*) AS n FROM evento_riesgo GROUP BY nivel"), engine
    )


try:
    data = cargar_datos()
    st.success("Datos cargados con exito desde PostgreSQL")
except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.stop()

st.write(data)

# ---------------------------------------------------------------------------
# Vista previa
# ---------------------------------------------------------------------------
st.write(data.head())
st.write("**Dimensiones de los datos:**")
st.write(f"Filas: {data.shape[0]}, Columnas: {data.shape[1]}")

# ---------------------------------------------------------------------------
# Estadisticas descriptivas
# ---------------------------------------------------------------------------
st.header("Estadisticas descriptivas")
st.dataframe(data.drop(columns=["Fecha_hora"]).describe(include="all").astype(str))

# ---------------------------------------------------------------------------
# Tablas dinamicas
# ---------------------------------------------------------------------------
# Solo columnas de baja cardinalidad para que la tabla no explote de tamano.
opciones_pivote = ["Calidad", "Dispositivo", "Franja", "Hora", "Fecha"]
opciones_pivote = [c for c in opciones_pivote if c in data.columns]

st.header("Tablas dinamicas")
col1, col2 = st.columns(2)
with col1:
    var_filas = st.selectbox("Variable para filas", options=opciones_pivote, index=0, key="rows")
with col2:
    var_cols = st.selectbox(
        "Variable para columnas", options=opciones_pivote,
        index=min(2, len(opciones_pivote) - 1), key="cols",
    )

if var_filas and var_cols:
    tabla_dinamica = data.pivot_table(
        index=var_filas, columns=var_cols, aggfunc="size", fill_value=0
    )
    st.write("Tabla dinamica (conteo de registros):")
    st.dataframe(tabla_dinamica)

# ---------------------------------------------------------------------------
# Graficos de distribucion
# ---------------------------------------------------------------------------
st.header("Graficos")
st.subheader("Graficos de distribucion")

columnas_numericas = data.select_dtypes(include=["number"]).columns
columnas_categoricas = data.select_dtypes(include=["object", "category"]).columns

if len(columnas_numericas) > 0:
    col_num = st.selectbox(
        "Selecciona una columna numerica", options=columnas_numericas, key="num_col"
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(data[col_num].dropna(), kde=True, color="#e4572e", ax=ax)
    ax.set_title(f"Distribucion de {col_num}")
    st.pyplot(fig)

if len(columnas_categoricas) > 0:
    col_cat = st.selectbox(
        "Selecciona una columna categorica", options=columnas_categoricas, key="cat_col"
    )
    conteo = data[col_cat].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=conteo.index, y=conteo.values, hue=conteo.index, palette="viridis", legend=False, ax=ax)
    ax.set_title(f"Conteo de {col_cat}")
    ax.set_ylabel("count")
    plt.xticks(rotation=30)
    st.pyplot(fig)

# ---------------------------------------------------------------------------
# Matriz de correlacion
# ---------------------------------------------------------------------------
st.subheader("Matriz de correlacion")
if len(columnas_numericas) > 1:
    matriz_corr = data[columnas_numericas].corr()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(matriz_corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Matriz de correlacion")
    st.pyplot(fig)
    st.caption(
        "El CO y la humedad de suelo estan correlacionados negativamente: "
        "suelo mas seco -> mas riesgo de combustion."
    )

# ---------------------------------------------------------------------------
# Limpieza basica
# ---------------------------------------------------------------------------
st.header("Limpieza basica")

RANGOS_FISICOS = {"CO_ppm": (0, 1000), "Humedad_suelo": (0, 100)}

nulos = int(data[["CO_ppm", "Humedad_suelo"]].isnull().sum().sum())
duplicados = int(data.duplicated(subset=["Fecha_hora"]).sum())
fuera_rango = 0
for columna, (minimo, maximo) in RANGOS_FISICOS.items():
    fuera_rango += int(((data[columna] < minimo) | (data[columna] > maximo)).sum())

c1, c2, c3 = st.columns(3)
c1.metric("Valores nulos", nulos)
c2.metric("Filas duplicadas", duplicados)
c3.metric("Valores fuera de rango fisico", fuera_rango)

if st.checkbox("Aplicar limpieza (quitar duplicados, recortar rango fisico, interpolar nulos)"):
    data_limpia = data.drop_duplicates(subset=["Fecha_hora"]).copy()
    for columna, (minimo, maximo) in RANGOS_FISICOS.items():
        mask = (data_limpia[columna] < minimo) | (data_limpia[columna] > maximo)
        data_limpia.loc[mask, columna] = np.nan
    data_limpia[["CO_ppm", "Humedad_suelo"]] = (
        data_limpia[["CO_ppm", "Humedad_suelo"]].interpolate(limit=6).ffill().bfill()
    )
    st.success(
        f"Datos limpios: {len(data_limpia)} filas, "
        f"{int(data_limpia[['CO_ppm', 'Humedad_suelo']].isnull().sum().sum())} nulos restantes"
    )
    data = data_limpia

# ---------------------------------------------------------------------------
# Deteccion de valores atipicos (z-score e IQR)
# ---------------------------------------------------------------------------
st.header("Deteccion de valores atipicos")

col_a, col_b = st.columns(2)
umbral_z = col_a.slider("Umbral z-score", 2.0, 5.0, 3.0, 0.1)
factor_iqr = col_b.slider("Factor IQR", 1.0, 3.0, 1.5, 0.1)

resumen_atipicos = []
for columna in ["CO_ppm", "Humedad_suelo"]:
    serie = data[columna].dropna()

    z = (serie - serie.mean()) / serie.std()
    atip_z = serie[z.abs() > umbral_z]

    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    iqr = q3 - q1
    limite_inf, limite_sup = q1 - factor_iqr * iqr, q3 + factor_iqr * iqr
    atip_iqr = serie[(serie < limite_inf) | (serie > limite_sup)]

    resumen_atipicos.append(
        {
            "Variable": columna,
            "Atipicos z-score": len(atip_z),
            "Atipicos IQR": len(atip_iqr),
            "% del total": round(100 * len(atip_z) / len(serie), 2),
        }
    )

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(data["Fecha_hora"], data[columna], color="#999999", linewidth=0.8)
    idx_atip = data.loc[atip_iqr.index]
    ax.scatter(idx_atip["Fecha_hora"], idx_atip[columna], color="#c62828", s=25, label="atipico")
    ax.set_title(f"{columna} - valores atipicos (IQR)")
    ax.legend()
    st.pyplot(fig)

st.write(pd.DataFrame(resumen_atipicos))

# ---------------------------------------------------------------------------
# Filtros dinamicos
# ---------------------------------------------------------------------------
st.header("Filtros dinamicos")
st.write("Selecciona columnas para aplicar filtros:")
columnas_filtro = st.multiselect("Selecciona columnas", options=data.columns)

if columnas_filtro:
    filtros = {}
    for columna in columnas_filtro:
        if data[columna].dtype == "object":
            filtros[columna] = st.multiselect(
                f"Filtrar {columna}", options=sorted(data[columna].dropna().unique())
            )
        else:
            minimo = float(data[columna].min())
            maximo = float(data[columna].max())
            filtros[columna] = st.slider(
                f"Filtrar {columna}", minimo, maximo, (minimo, maximo)
            )

    datos_filtrados = data.copy()
    for columna, valor in filtros.items():
        if isinstance(valor, list):
            if valor:
                datos_filtrados = datos_filtrados[datos_filtrados[columna].isin(valor)]
        else:
            datos_filtrados = datos_filtrados[
                (datos_filtrados[columna] >= valor[0])
                & (datos_filtrados[columna] <= valor[1])
            ]

    st.write(f"Datos filtrados: {len(datos_filtrados)} filas")
    st.dataframe(datos_filtrados)

# ---------------------------------------------------------------------------
# Modelos de Machine Learning (2 algoritmos)
# ---------------------------------------------------------------------------
st.header("Modelos de Machine Learning")
st.write(
    "Se entrenan **dos modelos** con particion temporal 75/25 (sin fuga de datos)."
)

# Preparacion de variables: rezagos (lags), media movil, hora del dia.
# Se descartan lecturas fuera del rango fisico del sensor (no entrenar con datos corruptos).
ml = data[["Fecha_hora", "CO_ppm", "Humedad_suelo", "Hora"]].dropna().reset_index(drop=True)
ml = ml[
    ml["CO_ppm"].between(0, 1000) & ml["Humedad_suelo"].between(0, 100)
].reset_index(drop=True)
for k in (1, 2, 3, 6):
    ml[f"CO_lag{k}"] = ml["CO_ppm"].shift(k)
    ml[f"Hum_lag{k}"] = ml["Humedad_suelo"].shift(k)
ml["CO_media6"] = ml["CO_ppm"].rolling(6).mean()
ml["CO_tendencia"] = ml["CO_ppm"].diff()
ml = ml.dropna().reset_index(drop=True)

corte = int(len(ml) * 0.75)
columnas_x = [c for c in ml.columns if c not in ("Fecha_hora", "CO_ppm")]

tab_reg, tab_clf = st.tabs(["Modelo 1: Regresion (pronostico de CO)", "Modelo 2: Clasificacion (nivel de riesgo)"])

# ---- Modelo 1: Regresion --------------------------------------------------
with tab_reg:
    st.subheader("Random Forest Regressor - pronostico del CO del siguiente instante")
    y = ml["CO_ppm"].shift(-1)
    datos_reg = ml.assign(objetivo=y).dropna()
    X = datos_reg[columnas_x]
    y = datos_reg["objetivo"]
    corte_r = int(len(X) * 0.75)

    modelo_reg = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    modelo_reg.fit(X.iloc[:corte_r], y.iloc[:corte_r])
    pred = modelo_reg.predict(X.iloc[corte_r:])
    real = y.iloc[corte_r:]

    m1, m2, m3 = st.columns(3)
    m1.metric("MAE (ppm)", f"{mean_absolute_error(real, pred):.2f}")
    m2.metric("RMSE (ppm)", f"{np.sqrt(mean_squared_error(real, pred)):.2f}")
    m3.metric("R2", f"{r2_score(real, pred):.3f}")

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(datos_reg["Fecha_hora"].iloc[corte_r:], real.values, label="real", color="#3d7dca")
    ax.plot(datos_reg["Fecha_hora"].iloc[corte_r:], pred, label="prediccion", color="#e4572e")
    ax.set_title("CO real vs pronosticado (conjunto de prueba)")
    ax.legend()
    st.pyplot(fig)

    importancias = pd.Series(modelo_reg.feature_importances_, index=columnas_x).sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    importancias.tail(10).plot(kind="barh", color="#e4572e", ax=ax)
    ax.set_title("Importancia de variables")
    st.pyplot(fig)

# ---- Modelo 2: Clasificacion --------------------------------------------
with tab_clf:
    st.subheader("Random Forest Classifier - nivel de riesgo de combustion")

    # Etiqueta: indice de riesgo (CO alto + humedad baja) -> bajo/medio/alto/critico
    comp_co = np.clip((ml["CO_ppm"] - 9) / (100 - 9) * 100, 0, 100)
    comp_hum = 100 - np.clip((ml["Humedad_suelo"] - 12) / (45 - 12) * 100, 0, 100)
    indice = 0.6 * comp_co + 0.4 * comp_hum
    nivel = pd.cut(
        indice, [-0.1, 25, 50, 75, 100.1], labels=["bajo", "medio", "alto", "critico"]
    ).astype(str)

    datos_clf = ml.assign(objetivo=nivel.shift(-1)).dropna()
    Xc = datos_clf[columnas_x]
    yc = datos_clf["objetivo"]
    corte_c = int(len(Xc) * 0.75)

    modelo_clf = RandomForestClassifier(
        n_estimators=250, max_depth=14, random_state=42, n_jobs=-1, class_weight="balanced"
    )
    modelo_clf.fit(Xc.iloc[:corte_c], yc.iloc[:corte_c])
    pred_c = modelo_clf.predict(Xc.iloc[corte_c:])
    real_c = yc.iloc[corte_c:]

    m1, m2 = st.columns(2)
    m1.metric("Accuracy", f"{accuracy_score(real_c, pred_c):.3f}")
    m2.metric("F1 (macro)", f"{f1_score(real_c, pred_c, average='macro'):.3f}")

    etiquetas = ["bajo", "medio", "alto", "critico"]
    etiquetas = [e for e in etiquetas if e in set(real_c) | set(pred_c)]
    cm = confusion_matrix(real_c, pred_c, labels=etiquetas)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=etiquetas, yticklabels=etiquetas, ax=ax,
    )
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusion")
    st.pyplot(fig)

    importancias_c = pd.Series(modelo_clf.feature_importances_, index=columnas_x).sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    importancias_c.tail(10).plot(kind="barh", color="#3d7dca", ax=ax)
    ax.set_title("Importancia de variables")
    st.pyplot(fig)

# ---------------------------------------------------------------------------
# Resumen final
# ---------------------------------------------------------------------------
st.header("Resumen final")
eventos = contar_eventos_riesgo()
total_eventos = int(eventos["n"].sum()) if not eventos.empty else 0

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Numero de filas", data.shape[0])
        st.metric("Numero de columnas", data.shape[1])
    with col2:
        st.metric("Valores nulos", int(data.isnull().sum().sum()))
        st.metric("Eventos de riesgo registrados", total_eventos)

if not eventos.empty:
    st.write("Eventos de riesgo por nivel:")
    st.dataframe(eventos)
