import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.consent_service import ConsentService


@pytest.mark.integration
async def test_patient_consents_flow(client: AsyncClient, professional_token: str):
    """Verifica registro, persistencia y consulta de consentimientos informados del paciente."""
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

    # 2. Registrar consentimiento de investigación (tipo, estado, fecha, versión)
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
    consent_id = consent_data["consent_id"]
    assert consent_data["consent_type"] == "RESEARCH_DATA_REUSE"
    assert consent_data["consent_status"] == "GRANTED"
    assert consent_data["version"] == "1.0"
    assert consent_data["patient_id"] == patient_id
    assert "2026-10-21" in consent_data["consent_date"]

    # 3. Listar consentimientos del paciente
    list_res = await client.get(
        f"/api/v1/patients/{patient_id}/consents",
        headers=headers,
    )
    assert list_res.status_code == 200
    consents = list_res.json()
    assert len(consents) == 1
    assert consents[0]["consent_id"] == consent_id

    # 4. Consultar consentimiento específico
    single_res = await client.get(
        f"/api/v1/patients/{patient_id}/consents/{consent_id}",
        headers=headers,
    )
    assert single_res.status_code == 200
    assert single_res.json()["consent_id"] == consent_id
    assert single_res.json()["consent_type"] == "RESEARCH_DATA_REUSE"

    # 5. Actualizar consentimiento (PATCH)
    patch_res = await client.patch(
        f"/api/v1/patients/{patient_id}/consents/{consent_id}",
        json={"consent_status": "WITHDRAWN", "notes": "Consentimiento revocado por solicitud del familiar"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["consent_status"] == "WITHDRAWN"
    assert "revocado" in patch_res.json()["notes"]


@pytest.mark.integration
async def test_patient_consent_all_valid_statuses(client: AsyncClient, professional_token: str):
    """Verifica la aceptación de los tres estados: GRANTED, DENIED, WITHDRAWN."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-CSNT-STAT",
            "first_name": "Hugo",
            "last_name": "Soto",
            "date_of_birth": "1965-04-10",
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    for st in ["GRANTED", "DENIED", "WITHDRAWN"]:
        res = await client.post(
            f"/api/v1/patients/{patient_id}/consents",
            json={
                "consent_type": f"TYPE_{st}",
                "consent_status": st,
                "consent_date": "2026-10-22T09:00:00Z",
                "version": "1.0",
            },
            headers=headers,
        )
        assert res.status_code == 201
        assert res.json()["consent_status"] == st


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


@pytest.mark.integration
async def test_patient_consent_patient_not_found(client: AsyncClient, professional_token: str):
    """Verifica que registrar o consultar consentimiento para paciente inexistente retorne 404."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    fake_patient_id = uuid.uuid4()
    fake_consent_id = uuid.uuid4()

    post_res = await client.post(
        f"/api/v1/patients/{fake_patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "2026-10-21T10:00:00Z",
            "version": "1.0",
        },
        headers=headers,
    )
    assert post_res.status_code == 404
    assert post_res.json()["error"]["code"] == "ENTITY_NOT_FOUND"

    get_res = await client.get(
        f"/api/v1/patients/{fake_patient_id}/consents/{fake_consent_id}",
        headers=headers,
    )
    assert get_res.status_code == 404


@pytest.mark.integration
async def test_patient_consent_invalid_dates_and_empty_versions(client: AsyncClient, professional_token: str):
    """Verifica rechazo de fechas inválidas y versiones vacías."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-CSNT-VAL",
            "first_name": "Mario",
            "last_name": "Paredes",
            "date_of_birth": "1978-09-15",
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    # 1. Versión vacía
    res_empty_ver = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "2026-10-21T10:00:00Z",
            "version": "   ",
        },
        headers=headers,
    )
    assert res_empty_ver.status_code == 422

    # 2. Tipo vacío
    res_empty_type = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "   ",
            "consent_status": "GRANTED",
            "consent_date": "2026-10-21T10:00:00Z",
            "version": "1.0",
        },
        headers=headers,
    )
    assert res_empty_type.status_code == 422

    # 3. Fecha inválida
    res_invalid_date = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "fecha-invalida-123",
            "version": "1.0",
        },
        headers=headers,
    )
    assert res_invalid_date.status_code == 422


@pytest.mark.integration
async def test_patient_consent_history_preserved_and_not_overwritten(
    client: AsyncClient, professional_token: str
):
    """
    Verifica que al registrar nuevos consentimientos o versiones para un mismo paciente,
    el historial se conserve intacto sin sobrescribir ni eliminar registros previos.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-CSNT-HIST",
            "first_name": "Carmen",
            "last_name": "Lagos",
            "date_of_birth": "1982-12-01",
        },
        headers=headers,
    )
    patient_id = patient_res.json()["patient_id"]

    # Registrar versión 1.0 (GRANTED)
    res_v1 = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "2026-01-10T08:00:00Z",
            "version": "1.0",
            "notes": "Firma inicial",
        },
        headers=headers,
    )
    assert res_v1.status_code == 201

    # Registrar versión 2.0 (DENIED por cambio de términos)
    res_v2 = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "DENIED",
            "consent_date": "2026-06-15T08:00:00Z",
            "version": "2.0",
            "notes": "Rechazo de nueva cláusula",
        },
        headers=headers,
    )
    assert res_v2.status_code == 201

    # Registrar versión 2.1 (GRANTED tras aclaración)
    res_v3 = await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "2026-07-20T08:00:00Z",
            "version": "2.1",
            "notes": "Aceptación de enmienda 2.1",
        },
        headers=headers,
    )
    assert res_v3.status_code == 201

    # Consultar historial: deben existir los 3 registros
    hist_res = await client.get(
        f"/api/v1/patients/{patient_id}/consents",
        headers=headers,
    )
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 3
    versions = [c["version"] for c in history]
    assert "1.0" in versions
    assert "2.0" in versions
    assert "2.1" in versions


@pytest.mark.integration
async def test_consent_denied_or_withdrawn_not_treated_as_granted(
    client: AsyncClient, professional_token: str, db_session: AsyncSession
):
    """
    Verifica que un consentimiento en estado DENIED o WITHDRAWN nunca sea interpretado como GRANTED.
    """
    headers = {"Authorization": f"Bearer {professional_token}"}
    patient_res = await client.post(
        "/api/v1/patients",
        json={
            "patient_code": "PAC-CSNT-CHECK",
            "first_name": "Daniel",
            "last_name": "Bravo",
            "date_of_birth": "1990-01-25",
        },
        headers=headers,
    )
    patient_id = uuid.UUID(patient_res.json()["patient_id"])
    service = ConsentService(db_session)

    # 1. Sin consentimiento registrado
    assert await service.is_consent_granted(patient_id, "RESEARCH") is False

    # 2. Consentimiento DENIED
    await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "DENIED",
            "consent_date": "2026-02-01T10:00:00Z",
            "version": "1.0",
        },
        headers=headers,
    )
    assert await service.is_consent_granted(patient_id, "RESEARCH") is False

    # 3. Consentimiento GRANTED
    await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "GRANTED",
            "consent_date": "2026-03-01T10:00:00Z",
            "version": "1.1",
        },
        headers=headers,
    )
    assert await service.is_consent_granted(patient_id, "RESEARCH") is True

    # 4. Consentimiento WITHDRAWN posteriormente
    await client.post(
        f"/api/v1/patients/{patient_id}/consents",
        json={
            "consent_type": "RESEARCH",
            "consent_status": "WITHDRAWN",
            "consent_date": "2026-04-01T10:00:00Z",
            "version": "1.1",
        },
        headers=headers,
    )
    assert await service.is_consent_granted(patient_id, "RESEARCH") is False
