from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that GET /api/v1/health responds with expected status and service name."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "ok",
        "service": "sanjeevani-grid-backend",
    }


def test_root_endpoint():
    """Verify root documentation helper endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "health" in response.json()
