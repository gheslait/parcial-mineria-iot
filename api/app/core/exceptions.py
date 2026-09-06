"""
Excepciones de dominio.

Las capas internas (repositories, services) lanzan estas excepciones sin saber
nada de HTTP. `app.main` las traduce a códigos de estado en un único lugar.
"""
from __future__ import annotations


class ErrorDominio(Exception):
    """Raíz de todos los errores propios del dominio."""

    codigo_http: int = 400


class RecursoNoEncontrado(ErrorDominio):
    codigo_http = 404

    def __init__(self, recurso: str, referencia: object) -> None:
        super().__init__(f"{recurso} no encontrado: {referencia!r}")


class ErrorValidacion(ErrorDominio):
    """El dato viola una regla física/lógica (rango del sensor, formato, etc.)."""

    codigo_http = 422

    def __init__(self, detalle: str, *, campo: str | None = None) -> None:
        self.campo = campo
        super().__init__(detalle)


class ConflictoEstado(ErrorDominio):
    codigo_http = 409
