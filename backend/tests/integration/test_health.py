import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_health_endpoint(client: AsyncClient):
    """Comprueba el endpoint público /api/v1/health."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.integration
async def test_database_health_endpoint(client: AsyncClient):
    """Comprueba el endpoint /api/v1/health/database."""
    response = await client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "latency_ms" in data
