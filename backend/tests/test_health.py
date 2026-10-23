from fastapi.testclient import TestClient

from tests.conftest import make_client


def test_health_reports_database_and_postgis(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert body["postgis"].startswith("3.")


def test_health_is_503_when_database_unreachable():
    # Port 1 is never a Postgres server, so the connection is refused immediately.
    with make_client("postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none") as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable", "postgis": None}


def test_health_is_503_when_postgis_missing(empty_database_url: str):
    with make_client(empty_database_url) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "ok", "postgis": None}
