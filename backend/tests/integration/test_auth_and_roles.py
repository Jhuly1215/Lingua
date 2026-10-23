import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_get_me_with_valid_token(client: AsyncClient, professional_token: str):
    """Verifica consulta exitosa de perfil /me con token válido de profesional."""
    headers = {"Authorization": f"Bearer {professional_token}"}
    response = await client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "ana.profesional@lingua.neurotech.org"
    assert data["role"]["name"] == "professional"


@pytest.mark.integration
async def test_get_me_unauthorized_without_token(client: AsyncClient):
    """Verifica que petición sin cabecera retorne 401 UNAUTHENTICATED."""
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.integration
async def test_get_me_with_invalid_token(client: AsyncClient):
    """Verifica que token malformado retorne 401 UNAUTHENTICATED."""
    headers = {"Authorization": "Bearer bad.token.here"}
    response = await client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.integration
async def test_role_authorization_forbidden_for_researcher_on_patient_creation(
    client: AsyncClient,
    researcher_token: str,
):
    """Verifica que un rol no autorizado (researcher) reciba 403 al intentar registrar un paciente."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    payload = {
        "patient_code": "PAC-FORBIDDEN-01",
        "first_name": "Test",
        "last_name": "Unauthorized",
        "date_of_birth": "1980-01-01",
        "primary_language": "Español",
        "bilingual": False,
    }
    response = await client.post("/api/v1/patients", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"
