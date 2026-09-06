"""Configuración de pruebas: no requiere base de datos (pruebas de dominio puras)."""
import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://tester:tester@localhost:5432/test"
)
os.environ.setdefault("DB_SCHEMA", "combustion_riesgo")
