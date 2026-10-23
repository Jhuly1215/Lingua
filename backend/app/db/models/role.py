import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Role(Base, AuditMixin):
    """
    Catálogo de roles de usuario del sistema (roles).
    """
    __tablename__ = "roles"

    role_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
    )
