-- ============================================================================
-- 003_vistas.sql  —  Vistas analíticas para Streamlit y Power BI.
--   Power BI se conecta "directamente a PostgreSQL, sin datos cargados
--   manualmente" (Fase 4): estas vistas le dan tablas planas listas para usar.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- vw_lecturas_enriquecidas: una fila por lectura con todo el contexto
-- (sensor, tipo, dispositivo, grupo) ya resuelto por JOIN.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_lecturas_enriquecidas AS
SELECT
    l.id                AS id_lectura,
    l.medido_en,
    l.recibido_en,
    l.valor,
    l.unidad,
    l.crudo,
    l.calidad,
    s.id                AS id_sensor,
    s.etiqueta          AS sensor,
    ts.clave            AS tipo_sensor,
    ts.magnitud,
    ts.rango_min,
    ts.rango_max,
    d.id                AS id_dispositivo,
    d.codigo            AS dispositivo,
    d.ubicacion,
    g.id               AS id_grupo,
    g.nombre           AS grupo,
    g.numero           AS grupo_numero,
    date_trunc('hour', l.medido_en) AS hora,
    date_trunc('day',  l.medido_en) AS dia,
    EXTRACT(hour FROM l.medido_en)  AS hora_del_dia
FROM lectura l
JOIN sensor       s  ON s.id  = l.id_sensor
JOIN tipo_sensor  ts ON ts.id = s.id_tipo_sensor
JOIN dispositivo  d  ON d.id  = l.id_dispositivo
JOIN grupo        g  ON g.id  = d.id_grupo;

-- ----------------------------------------------------------------------------
-- vw_riesgo_por_hora: CO y humedad agregados por hora y dispositivo, con el
-- conteo de anomalías y eventos de riesgo de esa hora. Base del dashboard.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_riesgo_por_hora AS
WITH lect AS (
    SELECT
        d.id                              AS id_dispositivo,
        d.codigo                          AS dispositivo,
        time_bucket(INTERVAL '1 hour', l.medido_en) AS hora,
        ts.clave                          AS tipo,
        l.valor
    FROM lectura l
    JOIN sensor      s  ON s.id  = l.id_sensor
    JOIN tipo_sensor ts ON ts.id = s.id_tipo_sensor
    JOIN dispositivo d  ON d.id  = l.id_dispositivo
),
agg AS (
    SELECT
        id_dispositivo,
        dispositivo,
        hora,
        avg(valor) FILTER (WHERE tipo = 'MQ7')       AS co_prom_ppm,
        max(valor) FILTER (WHERE tipo = 'MQ7')       AS co_max_ppm,
        avg(valor) FILTER (WHERE tipo = 'HUM_SUELO') AS humedad_prom_pct,
        min(valor) FILTER (WHERE tipo = 'HUM_SUELO') AS humedad_min_pct,
        count(*)   FILTER (WHERE tipo = 'MQ7')       AS n_lecturas_co
    FROM lect
    GROUP BY id_dispositivo, dispositivo, hora
)
SELECT
    a.*,
    COALESCE(an.n_anomalias, 0) AS n_anomalias,
    COALESCE(ev.n_eventos, 0)   AS n_eventos_riesgo,
    ev.nivel_max
FROM agg a
LEFT JOIN (
    SELECT s.id_dispositivo,
           time_bucket(INTERVAL '1 hour', an.detectado_en) AS hora,
           count(*) AS n_anomalias
    FROM anomalia an
    JOIN sensor s ON s.id = an.id_sensor
    GROUP BY s.id_dispositivo, hora
) an ON an.id_dispositivo = a.id_dispositivo AND an.hora = a.hora
LEFT JOIN (
    SELECT id_dispositivo,
           time_bucket(INTERVAL '1 hour', detectado_en) AS hora,
           count(*) AS n_eventos,
           max(nivel) AS nivel_max
    FROM evento_riesgo
    GROUP BY id_dispositivo, hora
) ev ON ev.id_dispositivo = a.id_dispositivo AND ev.hora = a.hora;
