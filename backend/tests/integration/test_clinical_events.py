import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_clinical_events_flow(client: AsyncClient, professional_token: str):
    """Verifica registro y consulta de eventos clínicos neurológicos asociados a un paciente."""
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear un paciente previo
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-EVT-01",
            "first_name": "Gonzalo",
            "last_name": "Morales",
            "date_of_birth": "1960-11-05",
            "primary_language": "Español",
            "bilingual": False,
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    # 2. Registrar evento neurológico (ACV Isquémico)
    event_payload = {
        "event_type": "ACV Isquémico",
        "event_date": "2026-08-14",
        "description": "Oclusión de rama M2 de arteria cerebral media izquierda",
        "event_severity": "Moderada",
        "lesion_location": "Fronto-temporal perisilviana",
        "lesion_hemisphere": "Izquierdo",
    }
    event_res = await client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        json=event_payload,
        headers=headers,
    )
    assert event_res.status_code == 201
    event_data = event_res.json()
    assert event_data["event_type"] == "ACV Isquémico"
    assert event_data["lesion_hemisphere"] == "Izquierdo"

    # 3. Listar eventos del paciente
    list_res = await client.get(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=headers,
    )
    assert list_res.status_code == 200
    events = list_res.json()
    assert len(events) == 1
    assert events[0]["clinical_event_id"] == event_data["clinical_event_id"]


@pytest.mark.integration
async def test_clinical_event_patient_not_found(client: AsyncClient, professional_token: str):
    """Verifica que registrar un evento clínico para un paciente inexistente retorne 404."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_id = uuid.uuid4()
    payload = {
        "event_type": "TCE",
        "event_date": "2026-09-01",
    }
    res = await client.post(
        f"/api/v1/patients/{fake_id}/clinical-events",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ENTITY_NOT_FOUND"
