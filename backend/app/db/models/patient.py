import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, CheckConstraint, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.clinical_event import ClinicalEvent
    from app.db.models.consent import PatientConsent
    from app.db.models.evaluation import Evaluation


class Patient(Base, AuditMixin):
    """
    Información de identificación y características generales del paciente (patients).
    """
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("education_years >= 0", name="chk_patients_education_years"),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    education_years: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    occupation: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    handedness: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    primary_language: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Español",
    )
    bilingual: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    secondary_language: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    dialect_region: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    medical_record_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    clinical_background: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    clinical_events: Mapped[List["ClinicalEvent"]] = relationship(
        "ClinicalEvent",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(ClinicalEvent.event_date)",
    )
    consents: Mapped[List["PatientConsent"]] = relationship(
        "PatientConsent",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(PatientConsent.consent_date)",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(Evaluation.evaluation_date)",
    )
