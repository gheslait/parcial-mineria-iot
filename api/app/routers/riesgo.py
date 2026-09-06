"""Endpoints de solo lectura para `evento_riesgo` y `anomalia`."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import AnomaliaRepository, EventoRiesgoRepository
from app.schemas.riesgo import AnomaliaOut, EventoRiesgoOut

router = APIRouter(prefix="/api/v1", tags=["riesgo"])


@router.get("/eventos-riesgo", response_model=list[EventoRiesgoOut])
def eventos_riesgo(
    db: Session = Depends(get_db),
    id_dispositivo: int | None = Query(default=None),
    nivel: str | None = Query(default=None, description="bajo|medio|alto|critico"),
    estado: str | None = Query(default=None, description="abierto|reconocido|cerrado"),
    desde: datetime | None = Query(default=None),
    limite: int = Query(default=500, ge=1, le=5000),
):
    return EventoRiesgoRepository(db).listar_filtrado(
        id_dispositivo=id_dispositivo, nivel=nivel, estado=estado, desde=desde, limite=limite
    )


@router.get("/anomalias", response_model=list[AnomaliaOut])
def anomalias(
    db: Session = Depends(get_db),
    id_sensor: int | None = Query(default=None),
    metodo: str | None = Query(default=None, description="zscore|iqr|rango_fisico"),
    desde: datetime | None = Query(default=None),
    limite: int = Query(default=1000, ge=1, le=20000),
):
    return AnomaliaRepository(db).listar_filtrado(
        id_sensor=id_sensor, metodo=metodo, desde=desde, limite=limite
    )
