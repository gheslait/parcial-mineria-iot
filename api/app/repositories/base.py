"""
`BaseRepository[T]` — CRUD genérico reutilizado por herencia.

Encapsula las operaciones comunes (obtener, listar, crear, borrar) para
cualquier modelo ORM. Los repositorios concretos solo añaden consultas
específicas de su tabla.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import RecursoNoEncontrado

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    #: subclase de `Base` que maneja este repositorio (lo fija cada hijo).
    modelo: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- lectura ---------------------------------------------------------
    def obtener(self, id_: int) -> T | None:
        return self.db.get(self.modelo, id_)

    def obtener_o_404(self, id_: int) -> T:
        obj = self.obtener(id_)
        if obj is None:
            raise RecursoNoEncontrado(self.modelo.__name__, id_)
        return obj

    def listar(self, *, limite: int = 500, offset: int = 0) -> list[T]:
        stmt = select(self.modelo).limit(limite).offset(offset)
        return list(self.db.scalars(stmt))

    # ---- escritura ------------------------------------------------------
    def crear(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()      # asigna PK sin cerrar la transacción
        return obj

    def crear_muchos(self, objs: list[T]) -> list[T]:
        self.db.add_all(objs)
        self.db.flush()
        return objs

    def eliminar(self, obj: T) -> None:
        self.db.delete(obj)
        self.db.flush()
