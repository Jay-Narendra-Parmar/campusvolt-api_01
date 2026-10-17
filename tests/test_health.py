from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# GET /v1/health should return 200 with {"status": "ok"}.
def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
