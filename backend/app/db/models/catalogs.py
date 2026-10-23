import uuid
from typing import Optional
from decimal import Decimal
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, GUID, AuditMixin


class AphasiaType(Base, AuditMixin):
    """
    Catálogo de tipos de afasia y estados de clasificación clínica (aphasia_types).
    Debe permitir valores como 'Mixta' y 'No clasificada' sin obligar a clasificar.
    """
    __tablename__ = "aphasia_types"

    aphasia_type_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


class SeverityLevel(Base, AuditMixin):
    """
    Catálogo de niveles de severidad asociados a evaluaciones (severity_levels).
    Diferenciado de la severidad intrínseca del evento neurológico inicial.
    """
    __tablename__ = "severity_levels"

    severity_level_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    min_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    max_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
