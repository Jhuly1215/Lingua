import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, AuditMixin

if TYPE_CHECKING:
    from app.db.models.subtest import Subtest


# Tipo JSON híbrido: JSONB en PostgreSQL / Supabase, JSON estándar en SQLite
JSONVariant = JSON().with_variant(PG_JSONB, "postgresql")


class Item(Base, AuditMixin):
    """Ítems o estímulos que forman parte de una subprueba (items)."""
    __tablename__ = "items"

    item_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    subtest_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("subtests.subtest_id", ondelete="CASCADE"), nullable=False, index=True)
    item_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stimulus_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instruction_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    subtest: Mapped["Subtest"] = relationship("Subtest", back_populates="items")


class Response(Base, AuditMixin):
    """Respuestas dadas por el paciente durante la evaluación (responses)."""
    __tablename__ = "responses"
    __table_args__ = (
        CheckConstraint("response_time_ms >= 0", name="chk_responses_time_ms"),
        CheckConstraint("response_order > 0", name="chk_responses_order"),
        CheckConstraint("start_time_ms >= 0", name="chk_responses_start_time"),
        CheckConstraint("end_time_ms >= 0", name="chk_responses_end_time"),
    )

    response_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("items.item_id", ondelete="SET NULL"), nullable=True, index=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    is_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    examiner_observation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Audio(Base, AuditMixin):
    """Metadatos de grabaciones de audio relacionadas con evaluaciones y respuestas (audio)."""
    __tablename__ = "audio"

    audio_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False, index=True)
    response_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("responses.response_id", ondelete="SET NULL"), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_seconds: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Transcription(Base, AuditMixin):
    """Transcripciones generadas por ASR y posteriormente revisadas por un profesional (transcriptions)."""
    __tablename__ = "transcriptions"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_transcriptions_confidence"),
    )

    transcription_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    audio_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("audio.audio_id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    asr_model: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 5), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Annotation(Base, AuditMixin):
    """Anotaciones sobre segmentos o eventos identificados dentro de una transcripción (annotations)."""
    __tablename__ = "annotations"
    __table_args__ = (
        CheckConstraint("start_time_seconds >= 0", name="chk_annotations_start_time"),
        CheckConstraint("end_time_seconds >= 0", name="chk_annotations_end_time"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_annotations_confidence"),
    )

    annotation_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    transcription_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("transcriptions.transcription_id", ondelete="CASCADE"), nullable=False, index=True)
    annotation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time_seconds: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    end_time_seconds: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 5), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)


class LinguisticFeature(Base, AuditMixin):
    """Características cuantitativas extraídas del audio, transcripción o anotaciones (linguistic_features)."""
    __tablename__ = "linguistic_features"

    linguistic_feature_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False, index=True)
    transcription_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("transcriptions.transcription_id", ondelete="SET NULL"), nullable=True, index=True)
    feature_name: Mapped[str] = mapped_column(String(150), nullable=False)
    feature_category: Mapped[str] = mapped_column(String(100), nullable=False)  # acoustic, fluency, lexical, syntactic
    feature_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    feature_text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calculation_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # audio, transcription, hybrid
    model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class AIAnalysis(Base, AuditMixin):
    """Resultados generados por modelos de IA/ML sobre una evaluación (ai_analysis)."""
    __tablename__ = "ai_analysis"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_ai_analysis_confidence"),
    )

    ai_analysis_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False, index=True)
    transcription_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("transcriptions.transcription_id", ondelete="SET NULL"), nullable=True, index=True)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    input_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    result_json: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 5), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    professional_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Report(Base, AuditMixin):
    """Reportes finales de la evaluación (reports)."""
    __tablename__ = "reports"

    report_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False, index=True)
    clinical_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linguistic_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    professional_observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
