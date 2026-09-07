# Fase 4 — Power BI

| Archivo | Qué es |
|---|---|
| [`GUIA_POWERBI.md`](GUIA_POWERBI.md) | **Empieza aquí.** Paso a paso completo: conexión, modelo, relaciones, todas las medidas DAX y los 12 visuales (4 indicadores + 6 gráficos + 2 filtros). |
| `Riesgo Combustion.pbip` + carpetas `.SemanticModel` / `.Report` | Proyecto Power BI en formato texto. Trae el modelo ya armado (5 tablas + Calendario, relaciones, 12 medidas). Ábrelo en Power BI Desktop; si tu versión no lo carga, usa la guía. |
| `tema_riesgo.json` | Tema de colores (naranja CO · azul humedad · verde→rojo riesgo). Vista › Temas › Buscar temas. |

El dashboard consume estas vistas del esquema `combustion_riesgo` (creadas por
`api/scripts/init_db.py`): `vw_lecturas_enriquecidas`, `vw_riesgo_por_hora`,
`vw_eventos`, `vw_anomalias`, más la tabla `dispositivo`.

El entregable que pide el profesor es el **`.pbix`** — se obtiene con
*Archivo › Guardar como › .pbix* una vez armado.
