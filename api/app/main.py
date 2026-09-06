"""
Punto de entrada de la API (FastAPI).

`crear_app()` arma la aplicación: registra los routers y traduce las excepciones
de dominio a códigos HTTP en un único lugar (los routers/services nunca lo hacen).
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ErrorDominio
from app.routers import ROUTERS

logging.basicConfig(level=get_settings().log_level)


def crear_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="API — Monitoreo de riesgo de combustión (IoT)",
        description=(
            "Fase 2 del parcial integrador de Minería de Datos. Recibe lecturas del "
            "ESP32 (MQ7 + humedad de suelo), valida tipo/rango/formato, almacena en "
            "PostgreSQL + TimescaleDB y evalúa el riesgo de combustión."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        app.include_router(router)

    @app.exception_handler(ErrorDominio)
    async def _dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
        cuerpo: dict = {"error": type(exc).__name__, "detalle": str(exc)}
        campo = getattr(exc, "campo", None)
        if campo:
            cuerpo["campo"] = campo
        return JSONResponse(status_code=exc.codigo_http, content=cuerpo)

    @app.get("/", tags=["salud"])
    def raiz() -> dict:
        return {
            "servicio": "monitoreo-riesgo-combustion",
            "docs": "/docs",
            "health": "/health",
            "grupo": settings.grupo_nombre,
        }

    return app


app = crear_app()
