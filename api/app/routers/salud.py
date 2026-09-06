"""`GET /health` — verifica conexión a la BD y presencia de TimescaleDB."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["salud"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    fila = db.execute(
        text("select extversion from pg_extension where extname = 'timescaledb'")
    ).scalar()
    pg = db.execute(text("select current_setting('server_version')")).scalar()
    return {
        "status": "ok",
        "postgresql": pg,
        "timescaledb": fila is not None,
        "timescaledb_version": fila,
        "schema": get_settings().db_schema_seguro,
    }
