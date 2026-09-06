"""Endpoints de solo lectura sobre catálogos y entidades maestras."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import (
    DispositivoRepository,
    GrupoRepository,
    ReglaRiesgoRepository,
    SensorRepository,
    TipoSensorRepository,
)
from app.schemas.catalogos import (
    DispositivoOut,
    GrupoOut,
    ReglaRiesgoOut,
    SensorOut,
    TipoSensorOut,
)

router = APIRouter(prefix="/api/v1", tags=["catalogos"])


@router.get("/grupos", response_model=list[GrupoOut])
def grupos(db: Session = Depends(get_db)):
    return GrupoRepository(db).listar()


@router.get("/dispositivos", response_model=list[DispositivoOut])
def dispositivos(db: Session = Depends(get_db)):
    return DispositivoRepository(db).listar()


@router.get("/tipos-sensor", response_model=list[TipoSensorOut])
def tipos_sensor(db: Session = Depends(get_db)):
    return TipoSensorRepository(db).listar()


@router.get("/sensores", response_model=list[SensorOut])
def sensores(db: Session = Depends(get_db)):
    return SensorRepository(db).listar()


@router.get("/reglas-riesgo", response_model=list[ReglaRiesgoOut])
def reglas_riesgo(db: Session = Depends(get_db)):
    return ReglaRiesgoRepository(db).listar()
