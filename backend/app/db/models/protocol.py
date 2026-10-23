import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.subtest import Subtest
    from app.db.models.evaluation import Evaluation


class Protocol(Base, AuditMixin):
    """
    Protocolos de evaluación disponibles en LINGUA (protocols).
    """
    __tablename__ = "protocols"

    protocol_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    subtests: Mapped[List["Subtest"]] = relationship(
        "Subtest",
        back_populates="protocol",
        cascade="all, delete-orphan",
        order_by="Subtest.order_number",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="protocol",
    )
