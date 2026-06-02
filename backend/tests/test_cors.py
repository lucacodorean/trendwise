from fastapi.testclient import TestClient

from app.main import app


def test_allows_expo_web_origin_for_browser_requests() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://localhost:8081"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"
