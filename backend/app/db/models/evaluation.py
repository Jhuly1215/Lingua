import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.patient import Patient
    from app.db.models.user import User
    from app.db.models.protocol import Protocol
    from app.db.models.clinical_event import ClinicalEvent
    from app.db.models.catalogs import AphasiaType, SeverityLevel
    from app.db.models.subtest import Subtest


class Evaluation(Base, AuditMixin):
    """
    Cabecera de cada evaluación realizada a un paciente (evaluations).
    Vincula paciente, profesional evaluador, protocolo y contexto clínico.
    """
    __tablename__ = "evaluations"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluator_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    protocol_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("protocols.protocol_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    clinical_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("clinical_events.clinical_event_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    aphasia_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("aphasia_types.aphasia_type_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity_level_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("severity_levels.severity_level_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
        index=True,
    )
    general_observations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", back_populates="evaluations")
    evaluator: Mapped["User"] = relationship("User", back_populates="evaluations")
    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="evaluations")
    clinical_event: Mapped[Optional["ClinicalEvent"]] = relationship("ClinicalEvent", back_populates="evaluations")
    aphasia_type: Mapped[Optional["AphasiaType"]] = relationship("AphasiaType")
    severity_level: Mapped[Optional["SeverityLevel"]] = relationship("SeverityLevel")
    evaluation_subtests: Mapped[List["EvaluationSubtest"]] = relationship(
        "EvaluationSubtest",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class EvaluationSubtest(Base, AuditMixin):
    """
    Tabla intermedia que vincula una evaluación con las subpruebas aplicadas (evaluation_subtests).
    duration_seconds permite registrar la duración efectiva en segundos (ej. 60 o 90s en FAS).
    """
    __tablename__ = "evaluation_subtests"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "subtest_id", name="uq_evaluation_subtests_eval_subtest"),
        CheckConstraint("duration_seconds > 0", name="chk_evaluation_subtests_duration"),
    )

    evaluation_subtest_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subtest_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("subtests.subtest_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    duration_seconds: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    observations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="evaluation_subtests")
    subtest: Mapped["Subtest"] = relationship("Subtest", back_populates="evaluation_subtests")
