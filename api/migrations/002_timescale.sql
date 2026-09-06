-- ============================================================================
-- 002_timescale.sql  —  Convierte `lectura` en hypertable y crea el agregado
--                       continuo. Se ejecuta DESPUÉS de crear las 9 tablas
--                       (Base.metadata.create_all en scripts/init_db.py).
--
-- El `search_path` ya viene fijado al schema del grupo por init_db.py.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ----------------------------------------------------------------------------
-- Hypertable: particiona `lectura` por `medido_en`, un chunk por día.
-- `medido_en` forma parte de la PK compuesta (id, medido_en), requisito de
-- TimescaleDB para cualquier índice único de una hypertable.
-- ----------------------------------------------------------------------------
SELECT create_hypertable(
    'lectura', 'medido_en',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists       => TRUE,
    migrate_data        => TRUE
);

-- ----------------------------------------------------------------------------
-- Agregado continuo: promedio/min/max de cada sensor cada 15 minutos.
-- Alimenta a Streamlit / Power BI sin recalcular sobre millones de filas.
-- ----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS ca_lecturas_15min
WITH (timescaledb.continuous) AS
SELECT
    id_sensor,
    time_bucket(INTERVAL '15 minutes', medido_en) AS bucket,
    avg(valor)   AS valor_prom,
    min(valor)   AS valor_min,
    max(valor)   AS valor_max,
    count(*)     AS n_muestras
FROM lectura
GROUP BY id_sensor, bucket
WITH NO DATA;

-- Refresco automático del agregado.
SELECT add_continuous_aggregate_policy(
    'ca_lecturas_15min',
    start_offset      => INTERVAL '3 days',
    end_offset        => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists     => TRUE
);

-- Compresión de chunks viejos (opcional pero muestra uso real de TimescaleDB).
ALTER TABLE lectura SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'id_sensor'
);
SELECT add_compression_policy('lectura', INTERVAL '14 days', if_not_exists => TRUE);
