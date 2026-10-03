from fastapi.testclient import TestClient
import pytest

from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path):
    """Crea un cliente de pruebas aislado con una base de datos temporal."""
    settings.database_url = f"sqlite:///{tmp_path / 'community-test.db'}"
    settings.api_key = "test-api-key"
    settings.bot_token = ""

    with TestClient(app) as test_client:
        yield test_client


def test_health_requires_api_key(client):
    """Comprueba que el endpoint de salud rechace peticiones sin credencial."""
    response = client.get("/health")

    assert response.status_code == 401


def test_health_reports_database_connection(client):
    """Comprueba que la API informe correctamente de SQLite disponible."""
    response = client.get("/health", headers={"X-API-Key": "test-api-key"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_project_proposal_is_saved(client):
    """Comprueba que una propuesta válida se persista y devuelva su ID."""
    response = client.post(
        "/api/project-proposals",
        headers={"X-API-Key": "test-api-key"},
        json={
            "name": "CI/CD demo",
            "manager": "Instructor",
            "description": "Proposal created by the integration test.",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
