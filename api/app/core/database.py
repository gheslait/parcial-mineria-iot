"""
Capa de infraestructura de base de datos.

- `engine`   : único motor SQLAlchemy del proceso (pool con `pool_pre_ping`).
- `Base`     : clase declarativa de la que heredan los 9 modelos ORM.
- `get_db()` : dependencia de FastAPI que entrega una sesión y la cierra.

El `search_path` se fija por conexión al schema del grupo, de modo que los
modelos ORM no necesitan calificar el nombre de cada tabla.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,      # revalida conexiones (servidor remoto)
    pool_size=5,
    max_overflow=5,
    future=True,
    # Fija el schema del grupo al abrir la conexión (no transaccional, robusto).
    connect_args={"options": f"-csearch_path={_settings.db_schema_seguro},public"},
)


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos ORM."""

    metadata_schema = _settings.db_schema_seguro  # documentativo; el schema real lo pone search_path


def get_db() -> Iterator[Session]:
    """Dependencia FastAPI: abre una sesión por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
