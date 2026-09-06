"""Routers FastAPI (capa HTTP): solo (de)serializan y delegan en services/repositories."""
from app.routers import catalogos, ingesta, lecturas, riesgo, salud

ROUTERS = [salud.router, ingesta.router, lecturas.router, catalogos.router, riesgo.router]

__all__ = ["ROUTERS"]
