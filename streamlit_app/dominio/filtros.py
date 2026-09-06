"""Filtros dinámicos compartidos por todas las vistas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Filtros:
    desde: date
    hasta: date
    tipos: tuple[str, ...]
    dispositivo: str | None
    valor_min: float | None
    valor_max: float | None
    calidad: str

    @property
    def ts_desde(self) -> str:
        return f"{self.desde} 00:00:00"

    @property
    def ts_hasta(self) -> str:
        return f"{self.hasta} 23:59:59"

    def clave_cache(self) -> tuple:
        """Tupla hashable para invalidar caché cuando cambian los filtros."""
        return (
            str(self.desde), str(self.hasta), self.tipos, self.dispositivo,
            self.valor_min, self.valor_max, self.calidad,
        )
