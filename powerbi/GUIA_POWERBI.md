# Fase 4 — Dashboard en Power BI

Dashboard ejecutivo del sistema de monitoreo de **riesgo de combustión**,
conectado **directamente a PostgreSQL** (sin datos cargados manualmente).

Requisito de la rúbrica: archivo `.pbix` conectado a PostgreSQL con
**4 indicadores + 6 gráficos + 2 filtros**, con estilo y colores acordes.

> ⚠️ **Importante:** el `.pbix` es un binario que **solo se genera en Power BI
> Desktop**. Este proyecto trae un `.pbip` (formato de texto) con el modelo ya
> armado, pero **no se pudo probar en un Power BI real**, así que puede requerir
> ajustes al abrir. La **Opción B** (construir desde cero con esta guía) es el
> camino seguro y toma ~30 min. Además te conviene para la sustentación:
> el profesor pregunta y hay que saber explicar el modelo.

---

## 0. Requisitos previos

1. **Power BI Desktop** (gratis, Microsoft Store o descarga directa).
2. **Conector de PostgreSQL**: Power BI Desktop reciente ya lo trae. Si al
   conectar pide *"instale el proveedor de datos Npgsql"*, instala
   **Npgsql** (versión *con* soporte para GAC / "Npgsql X.X.X.msi") y reinicia
   Power BI.
3. La base ya debe tener datos:
   ```
   python api/scripts/init_db.py
   python api/scripts/seed_historico.py --dias 20
   ```
4. Datos de conexión (los mismos de `api/.env`):
   - **Servidor:** `gheslait.com:15432`
   - **Base de datos:** `timescaledb`
   - **Esquema:** `combustion_riesgo`
   - Usuario / contraseña: los que tienes en `.env` (Power BI los guarda
     fuera del archivo; los pide la primera vez).

---

## 1. Opción A — abrir el proyecto incluido (`.pbip`)

1. Power BI Desktop → **Archivo › Abrir** → `powerbi/Riesgo Combustion.pbip`.
   (Si no ves proyectos `.pbip`: *Archivo › Opciones › Características de vista
   previa › "Guardar como proyecto de Power BI"* activado, y reinicia.)
2. Al cargar pedirá credenciales de PostgreSQL → método **Básico** → usuario y
   contraseña. Nivel de privacidad: *Organizational* u *Public*.
3. Si Power BI ofrece **actualizar el formato del informe**, acepta.
4. Ya tienes el **modelo completo** (5 tablas + `Calendario`, relaciones y
   todas las medidas DAX). Faltan solo los **visuales** → pasa al **paso 4**.

> Si el `.pbip` no abre en tu versión de Power BI, no pasa nada: usa la
> **Opción B**. Todo el contenido (M y DAX) está más abajo listo para pegar.

---

## 2. Opción B — construir el modelo desde cero

### 2.1 Conectar y cargar las vistas

**Inicio › Obtener datos › Base de datos PostgreSQL**
- Servidor: `gheslait.com:15432`
- Base de datos: `timescaledb`
- Modo: **Importar**

En el **Navegador**, marca (esquema `combustion_riesgo`):
- `vw_lecturas_enriquecidas`
- `vw_riesgo_por_hora`
- `vw_eventos`
- `vw_anomalias`
- `dispositivo`

→ **Transformar datos** (abre Power Query).

### 2.2 Renombrar y ajustar tipos

Renombra las consultas (clic derecho › Cambiar nombre):

| Consulta origen | Nombre |
|---|---|
| vw_lecturas_enriquecidas | `Lecturas` |
| vw_riesgo_por_hora | `RiesgoPorHora` |
| vw_eventos | `Eventos` |
| vw_anomalias | `Anomalias` |
| dispositivo | `Dispositivos` |

En **`Lecturas`, `RiesgoPorHora`, `Eventos`, `Anomalias`**: selecciona la
columna **`dia`** → menú tipo de dato → **Fecha/hora** (quita la zona horaria).
Haz lo mismo con `medido_en` / `detectado_en` / `hora` según exista.

> Alternativa: pega esto en el editor avanzado de cada consulta (reemplaza el
> nombre de la vista):
> ```
> let
>     Origen = PostgreSQL.Database("gheslait.com:15432", "timescaledb"),
>     Vista = Origen{[Schema="combustion_riesgo", Item="vw_lecturas_enriquecidas"]}[Data],
>     Tipos = Table.TransformColumnTypes(Vista, {{"medido_en", type datetime}, {"dia", type datetime}})
> in
>     Tipos
> ```

**Cerrar y aplicar.**

### 2.3 Tabla de calendario

**Modelado › Nueva tabla**:
```DAX
Calendario =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2026, 8, 1 ), DATE ( 2026, 10, 1 ) ),
    "Año", YEAR ( [Date] ),
    "MesNº", MONTH ( [Date] ),
    "Mes", FORMAT ( [Date], "mmm yyyy" ),
    "Día", DAY ( [Date] )
)
```
Selecciona la tabla → **Herramientas de tabla › Marcar como tabla de fechas**
→ columna `Date`. Ordena `Mes` por `MesNº` (Herramientas de columna).

### 2.4 Relaciones

**Vista de modelo**. Crea (arrastrando columna a columna):

| Desde (muchos) | Hacia (uno) | Dirección |
|---|---|---|
| `Lecturas[dia]` | `Calendario[Date]` | sencilla |
| `RiesgoPorHora[dia]` | `Calendario[Date]` | sencilla |
| `Eventos[dia]` | `Calendario[Date]` | sencilla |
| `Anomalias[dia]` | `Calendario[Date]` | sencilla |
| `Lecturas[dispositivo]` | `Dispositivos[codigo]` | sencilla |
| `RiesgoPorHora[dispositivo]` | `Dispositivos[codigo]` | sencilla |
| `Eventos[dispositivo]` | `Dispositivos[codigo]` | sencilla |
| `Anomalias[dispositivo]` | `Dispositivos[codigo]` | sencilla |

### 2.5 Medidas DAX

Clic derecho en `Lecturas` › **Nueva medida** (una por una):

```DAX
CO Promedio (ppm) = CALCULATE ( AVERAGE ( Lecturas[valor] ), Lecturas[tipo_sensor] = "MQ7" )
```
```DAX
CO Máximo (ppm) = CALCULATE ( MAX ( Lecturas[valor] ), Lecturas[tipo_sensor] = "MQ7" )
```
```DAX
Humedad Promedio (%) = CALCULATE ( AVERAGE ( Lecturas[valor] ), Lecturas[tipo_sensor] = "HUM_SUELO" )
```
```DAX
Humedad Mínima (%) = CALCULATE ( MIN ( Lecturas[valor] ), Lecturas[tipo_sensor] = "HUM_SUELO" )
```
```DAX
Lecturas Totales = COUNTROWS ( Lecturas )
```
```DAX
% Sospechosas =
DIVIDE (
    CALCULATE ( COUNTROWS ( Lecturas ), Lecturas[calidad] <> "valida" ),
    [Lecturas Totales]
)
```
```DAX
Eventos de Riesgo = COUNTROWS ( Eventos )
```
```DAX
Eventos Alto/Crítico =
CALCULATE ( [Eventos de Riesgo], Eventos[nivel] IN { "alto", "critico" } )
```
```DAX
Anomalías Detectadas = COUNTROWS ( Anomalias )
```
```DAX
Índice de Riesgo (prom) = AVERAGE ( RiesgoPorHora[riesgo_score] )
```
```DAX
Índice de Riesgo (máx) = MAX ( RiesgoPorHora[riesgo_score] )
```
```DAX
Nivel de Riesgo Actual =
SWITCH (
    TRUE (),
    [Índice de Riesgo (prom)] >= 75, "CRÍTICO",
    [Índice de Riesgo (prom)] >= 50, "ALTO",
    [Índice de Riesgo (prom)] >= 25, "MEDIO",
    "BAJO"
)
```
Da formato: las de ppm/% a `0.0`; `% Sospechosas` a porcentaje; los conteos a
número entero (`#,0`).

---

## 3. Tema (colores acordes)

**Vista › Temas › Buscar temas** → `powerbi/tema_riesgo.json`.
(Naranja = CO/MQ7, azul = humedad, verde→amarillo→rojo = nivel de riesgo.)

---

## 4. Construir el reporte

Objetivo de rúbrica: **4 indicadores, 6 gráficos, 2 filtros**. Distribución en
2 páginas.

### Página 1 — "Resumen"

**2 filtros (segmentaciones):**

| # | Visual | Campo | Formato |
|---|---|---|---|
| F1 | Segmentación | `Calendario[Date]` | estilo **Entre** (control deslizante de fechas) |
| F2 | Segmentación | `Dispositivos[codigo]` | lista o desplegable |

**4 indicadores (tarjetas):**

| # | Visual | Campo |
|---|---|---|
| I1 | Tarjeta | `[CO Promedio (ppm)]` |
| I2 | Tarjeta | `[Humedad Promedio (%)]` |
| I3 | Tarjeta | `[Eventos Alto/Crítico]` |
| I4 | Tarjeta | `[Índice de Riesgo (prom)]`  (añade `[Nivel de Riesgo Actual]` como segunda tarjeta de texto si quieres) |

**3 gráficos:**

| # | Visual | Eje X | Valores | Notas |
|---|---|---|---|---|
| G1 | Gráfico de líneas | `RiesgoPorHora[hora]` | `co_prom_ppm`, `riesgo_score` | "CO y nivel de riesgo en el tiempo" |
| G2 | Gráfico de líneas | `RiesgoPorHora[hora]` | `humedad_prom_pct`, `humedad_min_pct` | "Humedad del suelo en el tiempo" |
| G3 | Gráfico de columnas agrupadas | `Eventos[nivel]` | `[Eventos de Riesgo]` | ordena por nivel; colores por nivel |

### Página 2 — "Detalle y anomalías"

**3 gráficos + 1 tabla:**

| # | Visual | Campos | Notas |
|---|---|---|---|
| G4 | Gráfico de barras agrupadas | Eje `Anomalias[metodo]`, valor `[Anomalías Detectadas]` | "Anomalías por método (z-score / IQR / rango físico)" |
| G5 | Gráfico de dispersión | X `co_prom_ppm`, Y `humedad_prom_pct`, Leyenda `nivel_max`, Tamaño `n_anomalias` (tabla `RiesgoPorHora`) | muestra la relación CO↑ + humedad↓ = riesgo |
| G6 | Columnas apiladas | Eje `Anomalias[dia]`, leyenda `Anomalias[metodo]`, valor `[Anomalías Detectadas]` | evolución diaria de anomalías |
| T1 | Tabla | `Eventos`: `detectado_en`, `nivel`, `score`, `valor_mq7`, `valor_humedad`, `regla`, `mensaje` | detalle de eventos de riesgo |

> Los 2 filtros de la página 1: para que apliquen también a la página 2,
> selecciónalos → **Formato › Sincronizar segmentaciones** → marca ambas
> páginas. (O usa un filtro de nivel de informe con `Calendario[Date]`.)

### Formato recomendado

- Fondo de página: gris muy claro (ya viene del tema).
- Títulos de cada visual en español, descriptivos.
- G3 y G6: asigna manualmente rojo=`critico`, naranja=`alto`,
  amarillo=`medio`, verde=`bajo`.
- Tarjetas: etiqueta de categoría visible, valor grande.

---

## 5. Guardar como `.pbix`

**Archivo › Guardar como** → tipo **Archivo de Power BI (`.pbix`)** →
`Dashboard Riesgo Combustion.pbix`. Ese es el entregable de la Fase 4.

(El `.pbip` y el `.pbix` conviven; el `.pbix` es el que pide el profesor.)

---

## 6. Mapa rúbrica → dashboard

| Requisito Fase 4 | Cumple con |
|---|---|
| `.pbix` conectado directo a PostgreSQL, sin carga manual | conexión PostgreSQL en modo Importar a las vistas del esquema `combustion_riesgo` |
| 4 indicadores | I1 CO prom · I2 Humedad prom · I3 Eventos alto/crítico · I4 Índice de riesgo |
| 6 gráficos | G1 líneas CO+riesgo · G2 líneas humedad · G3 columnas eventos/nivel · G4 barras anomalías/método · G5 dispersión CO vs humedad · G6 columnas apiladas anomalías/día |
| 2 filtros | F1 rango de fechas · F2 dispositivo |
| Estilo y colores acordes | tema `tema_riesgo.json` + colores por nivel de riesgo |

---

## 7. Actualizar los datos

Con el simulador o el ESP32 enviando lecturas, en Power BI Desktop:
**Inicio › Actualizar**. Para refresco automático hay que publicar al Servicio
de Power BI y configurar una puerta de enlace (fuera del alcance del parcial).
