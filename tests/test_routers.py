from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    """Testa a rota raiz (UI)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_health_check():
    """Testa a rota de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
