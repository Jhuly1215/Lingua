from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.clinical_event import ClinicalEventCreate
from app.schemas.consent import ConsentCreate
from app.schemas.evaluation import EvaluationCreate, EvaluationSubtestCreate
from app.schemas.patient import PatientCreate, PatientUpdate


@pytest.mark.unit
def test_patient_create_valid():
    """Valida que un esquema de creación de paciente válido se instancie correctamente."""
    patient = PatientCreate(
        patient_code="PAC-2026-0001",
        first_name="María",
        last_name="Flores",
        date_of_birth=date(1965, 4, 15),
        gender="Femenino",
        education_years=12,
        occupation="Profesora",
        handedness="Diestro",
        primary_language="Español",
        bilingual=False,
        dialect_region="Andina",
        clinical_background="Hipertensión arterial controlada",
    )
    assert patient.patient_code == "PAC-2026-0001"
    assert patient.education_years == 12
    assert patient.bilingual is False


@pytest.mark.unit
def test_patient_create_negative_education_fails():
    """Verifica que años de escolaridad negativos disparen ValidationError."""
    with pytest.raises(ValidationError):
        PatientCreate(
            patient_code="PAC-2026-0002",
            first_name="Juan",
            last_name="Pérez",
            date_of_birth=date(1970, 1, 1),
            education_years=-3,  # Inválido
        )


@pytest.mark.unit
def test_consent_create_valid_and_invalid_status():
    """Verifica validación de estados permitidos en consentimiento informado."""
    valid_consent = ConsentCreate(
        consent_type="RESEARCH",
        consent_status="GRANTED",
        consent_date=datetime.now(timezone.utc),
        version="1.0",
        notes="Consentimiento firmado presencialmente",
    )
    assert valid_consent.consent_status == "GRANTED"

    with pytest.raises(ValidationError):
        ConsentCreate(
            consent_type="RESEARCH",
            consent_status="UNKNOWN_STATUS",  # Inválido
            consent_date=datetime.now(timezone.utc),
            version="1.0",
        )


@pytest.mark.unit
def test_evaluation_subtest_duration_validation():
    """Verifica que duration_seconds de subprueba deba ser mayor a 0."""
    valid_subtest = EvaluationSubtestCreate(
        subtest_id=uuid.uuid4(),
        duration_seconds=Decimal("60.0"),
        score=Decimal("15.0"),
    )
    assert valid_subtest.duration_seconds == Decimal("60.0")

    with pytest.raises(ValidationError):
        EvaluationSubtestCreate(
            subtest_id=uuid.uuid4(),
            duration_seconds=Decimal("0.0"),  # Inválido: debe ser gt 0
        )
