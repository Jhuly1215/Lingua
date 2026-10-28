import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_clinical_events_flow(client: AsyncClient, professional_token: str):
    """Verifica registro, consulta y actualización de eventos clínicos neurológicos asociados a un paciente."""
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
    event_id = event_data["clinical_event_id"]
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
    assert events[0]["clinical_event_id"] == event_id

    # 4. Consultar evento clínico específico
    get_res = await client.get(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    single_event = get_res.json()
    assert single_event["clinical_event_id"] == event_id
    assert single_event["event_type"] == "ACV Isquémico"

    # 5. Actualizar evento clínico específico (PATCH)
    patch_res = await client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}",
        json={"event_severity": "Severa", "description": "Evolución con edema peri-lesional"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["event_severity"] == "Severa"
    assert updated_data["description"] == "Evolución con edema peri-lesional"


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


@pytest.mark.integration
async def test_clinical_event_get_and_update_not_found(client: AsyncClient, professional_token: str):
    """Verifica 404 cuando el evento clínico o el paciente no existen."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_patient_id = uuid.uuid4()
    fake_event_id = uuid.uuid4()

    # Paciente inexistente
    res = await client.get(
        f"/api/v1/patients/{fake_patient_id}/clinical-events/{fake_event_id}",
        headers=headers,
    )
    assert res.status_code == 404

    # Crear paciente pero consultar evento inexistente
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-EVT-02",
            "first_name": "Laura",
            "last_name": "Rios",
            "date_of_birth": "1980-05-12",
        },
        headers=headers,
    )
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["patient_id"]

    res_event_404 = await client.get(
        f"/api/v1/patients/{patient_id}/clinical-events/{fake_event_id}",
        headers=headers,
    )
    assert res_event_404.status_code == 404

    # Intentar actualizar evento inexistente
    res_patch_404 = await client.patch(
        f"/api/v1/patients/{patient_id}/clinical-events/{fake_event_id}",
        json={"event_severity": "Leve"},
        headers=headers,
    )
    assert res_patch_404.status_code == 404


@pytest.mark.integration
async def test_clinical_event_empty_event_type_rejected(client: AsyncClient, professional_token: str):
    """Verifica que un tipo de evento vacío sea rechazado con 422."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-EVT-03",
            "first_name": "Elena",
            "last_name": "Castro",
            "date_of_birth": "1975-03-20",
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    res = await client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        json={
            "event_type": "   ",
            "event_date": "2026-05-10",
        },
        headers=headers,
    )
    assert res.status_code == 422
