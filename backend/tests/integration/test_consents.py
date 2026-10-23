import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_patient_consents_flow(client: AsyncClient, professional_token: str):
    """Verifica registro y consulta de consentimientos informados del paciente."""
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear un paciente previo
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-CSNT-01",
            "first_name": "Rosa",
            "last_name": "Valdez",
            "date_of_birth": "1972-02-18",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Registrar consentimiento de investigación
    consent_payload = {
        "consent_type": "RESEARCH_DATA_REUSE",
        "consent_status": "GRANTED",
        "consent_date": "2026-10-21T10:00:00Z",
        "version": "1.0",
        "notes": "Autoriza uso de grabaciones anonimizadas para análisis computacional",
    }
    consent_res = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json=consent_payload,
        headers=headers,
    )
    assert consent_res.status_code == 201
    consent_data = consent_res.json()
    assert consent_data["consent_status"] == "GRANTED"
    assert consent_data["version"] == "1.0"

    # 3. Listar consentimientos
    list_res = await client.get(
        f"/api/v1/patients/{patient_id}/consents",
        headers=headers,
    )
    assert list_res.status_code == 200
    consents = list_res.json()
    assert len(consents) == 1
    assert consents[0]["consent_id"] == consent_data["consent_id"]


@pytest.mark.integration
async def test_patient_consent_invalid_status(client: AsyncClient, professional_token: str):
    """Verifica que un estado de consentimiento no reconocido retorne 422."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_id = uuid.uuid4()
    payload = {
        "consent_type": "RESEARCH",
        "consent_status": "INVALID_STATE",
        "consent_date": "2026-10-21T10:00:00Z",
        "version": "1.0",
    }
    res = await client.post(
        f"/api/v1/patients/{fake_id}/consents",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 422
