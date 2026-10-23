import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.role import Role
    from app.db.models.evaluation import Evaluation


class User(Base, AuditMixin):
    """
    Usuarios que acceden al sistema, vinculados a un rol (users).
    El identificador `user_id` corresponde al UUID del usuario autenticado en Supabase Auth (auth.users.id).
    Las contraseñas son gestionadas de forma segura por Supabase Auth; `password_hash` se mantiene para
    compatibilidad con el esquema relacional o proveedores alternativos.
    """
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Relaciones
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="evaluator",
        foreign_keys="Evaluation.evaluator_id",
    )
