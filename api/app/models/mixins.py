"""Mixins reutilizables por los modelos ORM (herencia horizontal)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Agrega `creado_en` con marca de tiempo del servidor."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PkEnteraMixin:
    """PK entera autoincremental para tablas de catálogo / maestras (bajo volumen)."""

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, sort_order=-100
    )


class PkGrandeMixin:
    """PK `bigint` para tablas de alto volumen (logs append-only)."""

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, sort_order=-100
    )
