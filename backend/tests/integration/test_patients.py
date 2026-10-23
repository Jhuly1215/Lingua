import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_patient_crud_flow(client: AsyncClient, professional_token: str):
    """Prueba el ciclo de vida completo de un paciente (Crear, Consultar, Listar, Actualizar, Borrado lógico)."""
    headers = {"Authorization": f"Bearer {professional_token}"}

    # 1. Crear Paciente
    create_payload = {
        "patient_code": "PAC-2026-0001",
        "first_name": "Elena",
        "last_name": "Sánchez",
        "date_of_birth": "1968-06-20",
        "gender": "Femenino",
        "education_years": 14,
        "occupation": "Contadora",
        "handedness": "Diestro",
        "primary_language": "Español",
        "bilingual": False,
        "dialect_region": "Andina",
        "medical_record_number": "HC-88492",
        "clinical_background": "Dislipidemia, hipertensión grado 1",
        "notes": "Buena disposición en la primera entrevista",
    }
    create_res = await client.post("/api/v1/patients", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    patient_id = created_data["patient_id"]
    assert created_data["patient_code"] == "PAC-2026-0001"
    assert created_data["active"] is True

    # 2. Consultar por ID
    get_res = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["first_name"] == "Elena"

    # 3. Listar y Buscar
    list_res = await client.get("/api/v1/patients?search=Elena", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(p["patient_id"] == patient_id for p in list_data["items"])

    # 4. Actualizar parcialmente (PATCH)
    patch_payload = {
        "occupation": "Contadora jubilada",
        "notes": "Seguimiento acordado para la próxima semana",
    }
    patch_res = await client.patch(f"/api/v1/patients/{patient_id}", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["occupation"] == "Contadora jubilada"

    # 5. Eliminación lógica
    del_res = await client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
    assert del_res.status_code == 204

    # Verificar que ya no sea retornado en consultas activas
    get_after_del = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert get_after_del.status_code == 404


@pytest.mark.integration
async def test_patient_duplicate_code_conflict(client: AsyncClient, professional_token: str):
    """Verifica que intentar registrar dos pacientes con el mismo código arroje 409 ENTITY_CONFLICT."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    payload = {
        "patient_code": "PAC-DUPLICATE-01",
        "first_name": "Mario",
        "last_name": "Ramos",
        "date_of_birth": "1975-03-10",
        "primary_language": "Español",
        "bilingual": False,
    }
    res1 = await client.post("/api/v1/patients", json=payload, headers=headers)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/patients", json=payload, headers=headers)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "ENTITY_CONFLICT"


@pytest.mark.integration
async def test_patient_not_found(client: AsyncClient, professional_token: str):
    """Verifica que un UUID inexistente retorne 404 ENTITY_NOT_FOUND."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_uuid = uuid.uuid4()
    response = await client.get(f"/api/v1/patients/{fake_uuid}", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ENTITY_NOT_FOUND"
