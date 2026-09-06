-- ============================================================================
-- 004_seed_catalogos.sql  —  Datos de catálogo del dominio (idempotente).
--   - tipo_sensor : las 2 magnitudes del grupo (MQ7 + humedad de suelo).
--   - regla_riesgo: reglas simples del motor de evaluación de combustión.
--   El grupo, el dispositivo y sus sensores los crea scripts/init_db.py a
--   partir de api/.env (identidad específica del despliegue).
-- ============================================================================

INSERT INTO tipo_sensor (clave, nombre, magnitud, unidad, rango_min, rango_max, precision, descripcion)
VALUES
  ('MQ7', 'Sensor de monoxido de carbono MQ-7', 'Monoxido de carbono', 'ppm',
   0, 1000, 1,
   'Gas MQ-7. El CO es producto de combustion incompleta; su aumento anticipa fuego latente.'),
  ('HUM_SUELO', 'Sensor resistivo de humedad de suelo', 'Humedad del suelo', '%',
   0, 100, 1,
   'Sonda resistiva. Suelo/hojarasca seco (baja humedad) eleva el riesgo de ignicion.')
ON CONFLICT (clave) DO UPDATE
  SET nombre = EXCLUDED.nombre,
      rango_min = EXCLUDED.rango_min,
      rango_max = EXCLUDED.rango_max,
      descripcion = EXCLUDED.descripcion;

INSERT INTO regla_riesgo (id_tipo_sensor, nombre, operador, umbral_min, umbral_max, nivel, puntaje, mensaje, prioridad, activo)
VALUES
  ((SELECT id FROM tipo_sensor WHERE clave = 'MQ7'),
   'CO moderado', 'ge', 25, NULL, 'medio', 15,
   'CO por encima de 25 ppm: posible combustion incipiente.', 30, TRUE),

  ((SELECT id FROM tipo_sensor WHERE clave = 'MQ7'),
   'CO alto', 'ge', 50, NULL, 'alto', 25,
   'CO alto (>50 ppm): combustion probable, verificar el area.', 20, TRUE),

  ((SELECT id FROM tipo_sensor WHERE clave = 'MQ7'),
   'CO critico', 'ge', 100, NULL, 'critico', 40,
   'CO critico (>100 ppm): riesgo de incendio activo.', 10, TRUE),

  ((SELECT id FROM tipo_sensor WHERE clave = 'HUM_SUELO'),
   'Suelo seco', 'le', 20, NULL, 'medio', 15,
   'Humedad de suelo < 20%: material combustible seco.', 30, TRUE),

  ((SELECT id FROM tipo_sensor WHERE clave = 'HUM_SUELO'),
   'Suelo muy seco', 'le', 12, NULL, 'alto', 25,
   'Humedad de suelo < 12%: alta facilidad de ignicion.', 20, TRUE)
ON CONFLICT (nombre) DO NOTHING;
