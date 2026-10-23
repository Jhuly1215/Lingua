import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.patient import Patient
    from app.db.models.evaluation import Evaluation


class ClinicalEvent(Base, AuditMixin):
    """
    Registra eventos clínicos relevantes asociados a un paciente (clinical_events).
    Diferencia la severidad del evento clínico de la severidad observada en la evaluación.
    """
    __tablename__ = "clinical_events"

    clinical_event_id: Mapped[uuid.UUID] = mapped_column(
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
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    event_severity: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    lesion_location: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )
    lesion_hemisphere: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", back_populates="clinical_events")
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="clinical_event",
    )
