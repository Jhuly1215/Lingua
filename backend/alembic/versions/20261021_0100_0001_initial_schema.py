"""initial_schema_v02

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. roles
    op.create_table(
        "roles",
        sa.Column("role_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # 2. users
    op.create_table(
        "users",
        sa.Column("user_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", sa.UUID(as_uuid=True), sa.ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    # 3. patients
    op.create_table(
        "patients",
        sa.Column("patient_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_code", sa.String(50), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(30), nullable=True),
        sa.Column("education_years", sa.Integer(), nullable=True),
        sa.Column("occupation", sa.String(150), nullable=True),
        sa.Column("handedness", sa.String(30), nullable=True),
        sa.Column("primary_language", sa.String(100), nullable=False, server_default="Español"),
        sa.Column("bilingual", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("secondary_language", sa.String(100), nullable=True),
        sa.Column("dialect_region", sa.String(100), nullable=True),
        sa.Column("medical_record_number", sa.String(100), nullable=True),
        sa.Column("clinical_background", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("education_years >= 0", name="chk_patients_education_years"),
    )
    op.create_index("ix_patients_patient_code", "patients", ["patient_code"])
    op.create_index("ix_patients_active", "patients", ["active"])

    # 4. clinical_events
    op.create_table(
        "clinical_events",
        sa.Column("clinical_event_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", sa.UUID(as_uuid=True), sa.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_severity", sa.String(50), nullable=True),
        sa.Column("lesion_location", sa.String(150), nullable=True),
        sa.Column("lesion_hemisphere", sa.String(30), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clinical_events_patient_id", "clinical_events", ["patient_id"])

    # 5. aphasia_types
    op.create_table(
        "aphasia_types",
        sa.Column("aphasia_type_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aphasia_types_name", "aphasia_types", ["name"])

    # 6. severity_levels
    op.create_table(
        "severity_levels",
        sa.Column("severity_level_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("max_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_severity_levels_name", "severity_levels", ["name"])

    # 7. protocols
    op.create_table(
        "protocols",
        sa.Column("protocol_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 8. subtests
    op.create_table(
        "subtests",
        sa.Column("subtest_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("protocol_id", sa.UUID(as_uuid=True), sa.ForeignKey("protocols.protocol_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("order_number", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_subtests_protocol_id", "subtests", ["protocol_id"])
    op.create_index("ix_subtests_code", "subtests", ["code"])

    # 9. items
    op.create_table(
        "items",
        sa.Column("item_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("subtest_id", sa.UUID(as_uuid=True), sa.ForeignKey("subtests.subtest_id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_number", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(50), nullable=True),
        sa.Column("stimulus_text", sa.Text(), nullable=True),
        sa.Column("instruction_text", sa.Text(), nullable=True),
        sa.Column("response_type", sa.String(50), nullable=True),
        sa.Column("order_number", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_items_subtest_id", "items", ["subtest_id"])

    # 10. evaluations
    op.create_table(
        "evaluations",
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", sa.UUID(as_uuid=True), sa.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluator_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("protocol_id", sa.UUID(as_uuid=True), sa.ForeignKey("protocols.protocol_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("clinical_event_id", sa.UUID(as_uuid=True), sa.ForeignKey("clinical_events.clinical_event_id", ondelete="SET NULL"), nullable=True),
        sa.Column("aphasia_type_id", sa.UUID(as_uuid=True), sa.ForeignKey("aphasia_types.aphasia_type_id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity_level_id", sa.UUID(as_uuid=True), sa.ForeignKey("severity_levels.severity_level_id", ondelete="SET NULL"), nullable=True),
        sa.Column("evaluation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), server_default="PENDING", nullable=False),
        sa.Column("general_observations", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluations_patient_id", "evaluations", ["patient_id"])
    op.create_index("ix_evaluations_evaluator_id", "evaluations", ["evaluator_id"])
    op.create_index("ix_evaluations_protocol_id", "evaluations", ["protocol_id"])

    # 11. evaluation_subtests
    op.create_table(
        "evaluation_subtests",
        sa.Column("evaluation_subtest_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("subtest_id", sa.UUID(as_uuid=True), sa.ForeignKey("subtests.subtest_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("score", sa.Numeric(10, 4), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("evaluation_id", "subtest_id", name="uq_evaluation_subtests_eval_subtest"),
        sa.CheckConstraint("duration_seconds > 0", name="chk_evaluation_subtests_duration"),
    )
    op.create_index("ix_evaluation_subtests_evaluation_id", "evaluation_subtests", ["evaluation_id"])
    op.create_index("ix_evaluation_subtests_subtest_id", "evaluation_subtests", ["subtest_id"])

    # 12. responses
    op.create_table(
        "responses",
        sa.Column("response_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.UUID(as_uuid=True), sa.ForeignKey("items.item_id", ondelete="SET NULL"), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("score", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("response_order", sa.Integer(), nullable=True),
        sa.Column("start_time_ms", sa.Integer(), nullable=True),
        sa.Column("end_time_ms", sa.Integer(), nullable=True),
        sa.Column("examiner_observation", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("response_time_ms >= 0", name="chk_responses_time_ms"),
        sa.CheckConstraint("response_order > 0", name="chk_responses_order"),
        sa.CheckConstraint("start_time_ms >= 0", name="chk_responses_start_time"),
        sa.CheckConstraint("end_time_ms >= 0", name="chk_responses_end_time"),
    )
    op.create_index("ix_responses_evaluation_id", "responses", ["evaluation_id"])

    # 13. audio
    op.create_table(
        "audio",
        sa.Column("audio_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("response_id", sa.UUID(as_uuid=True), sa.ForeignKey("responses.response_id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_format", sa.String(50), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(12, 4), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audio_evaluation_id", "audio", ["evaluation_id"])

    # 14. transcriptions
    op.create_table(
        "transcriptions",
        sa.Column("transcription_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("audio_id", sa.UUID(as_uuid=True), sa.ForeignKey("audio.audio_id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("corrected_text", sa.Text(), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("asr_model", sa.String(150), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Numeric(6, 5), nullable=True),
        sa.Column("processing_status", sa.String(50), server_default="PENDING", nullable=False),
        sa.Column("human_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reviewer_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_transcriptions_confidence"),
    )
    op.create_index("ix_transcriptions_audio_id", "transcriptions", ["audio_id"])

    # 15. annotations
    op.create_table(
        "annotations",
        sa.Column("annotation_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("transcription_id", sa.UUID(as_uuid=True), sa.ForeignKey("transcriptions.transcription_id", ondelete="CASCADE"), nullable=False),
        sa.Column("annotation_type", sa.String(100), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("start_time_seconds", sa.Numeric(12, 4), nullable=True),
        sa.Column("end_time_seconds", sa.Numeric(12, 4), nullable=True),
        sa.Column("confidence", sa.Numeric(6, 5), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("start_time_seconds >= 0", name="chk_annotations_start_time"),
        sa.CheckConstraint("end_time_seconds >= 0", name="chk_annotations_end_time"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_annotations_confidence"),
    )
    op.create_index("ix_annotations_transcription_id", "annotations", ["transcription_id"])

    # 16. linguistic_features
    op.create_table(
        "linguistic_features",
        sa.Column("linguistic_feature_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcription_id", sa.UUID(as_uuid=True), sa.ForeignKey("transcriptions.transcription_id", ondelete="SET NULL"), nullable=True),
        sa.Column("feature_name", sa.String(150), nullable=False),
        sa.Column("feature_category", sa.String(100), nullable=False),
        sa.Column("feature_value", sa.Numeric(18, 8), nullable=True),
        sa.Column("feature_text_value", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("calculation_method", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_linguistic_features_evaluation_id", "linguistic_features", ["evaluation_id"])

    # 17. ai_analysis
    op.create_table(
        "ai_analysis",
        sa.Column("ai_analysis_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcription_id", sa.UUID(as_uuid=True), sa.ForeignKey("transcriptions.transcription_id", ondelete="SET NULL"), nullable=True),
        sa.Column("model_name", sa.String(150), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("input_version", sa.String(100), nullable=True),
        sa.Column("result_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 5), nullable=True),
        sa.Column("processing_status", sa.String(50), server_default="PENDING", nullable=False),
        sa.Column("human_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("professional_interpretation", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="chk_ai_analysis_confidence"),
    )
    op.create_index("ix_ai_analysis_evaluation_id", "ai_analysis", ["evaluation_id"])

    # 18. reports
    op.create_table(
        "reports",
        sa.Column("report_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.evaluation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinical_summary", sa.Text(), nullable=True),
        sa.Column("linguistic_summary", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("professional_observations", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), server_default="DRAFT", nullable=False),
        sa.Column("approved_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_evaluation_id", "reports", ["evaluation_id"])

    # 19. patient_consents
    op.create_table(
        "patient_consents",
        sa.Column("consent_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", sa.UUID(as_uuid=True), sa.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("consent_status", sa.String(30), nullable=False),
        sa.Column("consent_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("consent_status IN ('GRANTED', 'DENIED', 'WITHDRAWN')", name="chk_patient_consents_status"),
    )
    op.create_index("ix_patient_consents_patient_id", "patient_consents", ["patient_id"])
    op.create_index("ix_patient_consents_consent_type", "patient_consents", ["consent_type"])


def downgrade() -> None:
    op.drop_table("patient_consents")
    op.drop_table("reports")
    op.drop_table("ai_analysis")
    op.drop_table("linguistic_features")
    op.drop_table("annotations")
    op.drop_table("transcriptions")
    op.drop_table("audio")
    op.drop_table("responses")
    op.drop_table("evaluation_subtests")
    op.drop_table("evaluations")
    op.drop_table("items")
    op.drop_table("subtests")
    op.drop_table("protocols")
    op.drop_table("severity_levels")
    op.drop_table("aphasia_types")
    op.drop_table("clinical_events")
    op.drop_table("patients")
    op.drop_table("users")
    op.drop_table("roles")
