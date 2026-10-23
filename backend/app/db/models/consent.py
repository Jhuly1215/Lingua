import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.patient import Patient


class PatientConsent(Base, AuditMixin):
    """
    Registra consentimientos asociados al paciente, especialmente para uso de datos en investigación (patient_consents).
    Conserva trazabilidad de versiones y estados (GRANTED, DENIED, WITHDRAWN).
    """
    __tablename__ = "patient_consents"
    __table_args__ = (
        CheckConstraint(
            "consent_status IN ('GRANTED', 'DENIED', 'WITHDRAWN')",
            name="chk_patient_consents_status",
        ),
    )

    consent_id: Mapped[uuid.UUID] = mapped_column(
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
    consent_type: Mapped[str] = mapped_column(
        String(50),  # ej. 'RESEARCH', 'EVALUATION', 'AUDIO_RECORDING'
        nullable=False,
    )
    consent_status: Mapped[str] = mapped_column(
        String(30),  # 'GRANTED', 'DENIED', 'WITHDRAWN'
        nullable=False,
        index=True,
    )
    consent_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", back_populates="consents")
