"""`POST /api/v1/ingesta` — punto de entrada de los datos del ESP32."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ingesta import PayloadESP32, RespuestaIngesta
from app.services.ingesta_service import IngestaService

router = APIRouter(prefix="/api/v1", tags=["ingesta"])


@router.post(
    "/ingesta",
    response_model=RespuestaIngesta,
    status_code=status.HTTP_201_CREATED,
    summary="Recibe un lote de lecturas del ESP32 (JSON)",
)
def ingesta(payload: PayloadESP32, db: Session = Depends(get_db)) -> RespuestaIngesta:
    servicio = IngestaService(db)
    try:
        respuesta = servicio.procesar(payload)
        db.commit()
        return respuesta
    except Exception:
        db.rollback()
        raise
