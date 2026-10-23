import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.protocol import Protocol
    from app.db.models.pipeline import Item
    from app.db.models.evaluation import EvaluationSubtest


class Subtest(Base, AuditMixin):
    """
    Subpruebas que componen cada protocolo (subtests).
    """
    __tablename__ = "subtests"

    subtest_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    protocol_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("protocols.protocol_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    order_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relaciones
    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="subtests")
    items: Mapped[List["Item"]] = relationship(
        "Item",
        back_populates="subtest",
        cascade="all, delete-orphan",
        order_by="Item.order_number",
    )
    evaluation_subtests: Mapped[List["EvaluationSubtest"]] = relationship(
        "EvaluationSubtest",
        back_populates="subtest",
    )
