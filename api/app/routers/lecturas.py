"""`GET /api/v1/lecturas` — consulta de histórico con filtros dinámicos.

Streamlit se conecta directo a la BD, pero este endpoint queda disponible para
el resto del equipo (mismo contrato de filtros que `FiltroLecturas`).
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import LecturaRepository
from app.schemas.lectura import FiltroLecturas, LecturaOut

router = APIRouter(prefix="/api/v1", tags=["lecturas"])


@router.get("/lecturas", response_model=list[LecturaOut])
def listar_lecturas(
    db: Session = Depends(get_db),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    tipo_sensor: str | None = Query(default=None, description="MQ7 | HUM_SUELO"),
    codigo_dispositivo: str | None = Query(default=None),
    valor_min: float | None = Query(default=None),
    valor_max: float | None = Query(default=None),
    calidad: str | None = Query(default=None),
    limite: int = Query(default=1000, ge=1, le=50000),
) -> list[LecturaOut]:
    filtro = FiltroLecturas(
        desde=desde,
        hasta=hasta,
        tipo_sensor=tipo_sensor,
        codigo_dispositivo=codigo_dispositivo,
        valor_min=valor_min,
        valor_max=valor_max,
        calidad=calidad,
        limite=limite,
    )
    return LecturaRepository(db).filtrar(filtro)


@router.get("/lecturas/rango-fechas")
def rango_fechas(db: Session = Depends(get_db)) -> dict:
    minimo, maximo = LecturaRepository(db).rango_fechas()
    return {"desde": minimo, "hasta": maximo}
