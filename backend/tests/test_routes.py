import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def _reset_state():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _make_incident(client_id: str = "test-001", title: str = "Test Incident"):
    return {
        "client_id": client_id,
        "title": title,
        "created_at": "2026-09-19T10:00:00Z",
    }


class TestCreateIncident:
    def test_create_returns_200_with_server_id(self, client):
        resp = client.post("/api/incidents", json=_make_incident())
        assert resp.status_code == 200
        data = resp.json()
        assert data["client_id"] == "test-001"
        assert data["server_id"]
        assert data["was_duplicate"] is False

    def test_create_preserves_all_fields(self, client):
        payload = _make_incident(title="Fire in warehouse")
        resp = client.post("/api/incidents", json=payload)
        data = resp.json()
        assert data["title"] == "Fire in warehouse"
        assert data["created_at"] == "2026-09-19T10:00:00Z"
        assert data["received_at"]

    def test_create_with_empty_title_returns_422(self, client):
        payload = _make_incident(title="")
        resp = client.post("/api/incidents", json=payload)
        assert resp.status_code == 422


class TestListIncidents:
    def test_empty_store_returns_empty_list(self, client):
        resp = client.get("/api/incidents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_incidents_returned_in_insertion_order(self, client):
        for i in range(5):
            client.post("/api/incidents", json=_make_incident(
                client_id=f"order-{i:03d}",
                title=f"Incident {i}",
            ))
        resp = client.get("/api/incidents")
        ids = [inc["client_id"] for inc in resp.json()]
        assert ids == [f"order-{i:03d}" for i in range(5)]


class TestGetSingleIncident:
    def test_get_existing_incident(self, client):
        client.post("/api/incidents", json=_make_incident(client_id="lookup-001"))
        resp = client.get("/api/incidents/lookup-001")
        assert resp.status_code == 200
        assert resp.json()["client_id"] == "lookup-001"

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/incidents/does-not-exist")
        assert resp.status_code == 404


class TestClearIncidents:
    def test_clear_removes_all(self, client):
        for i in range(3):
            client.post("/api/incidents", json=_make_incident(client_id=f"clear-{i}"))
        assert len(client.get("/api/incidents").json()) == 3
        resp = client.delete("/api/incidents")
        assert resp.status_code == 204
        assert len(client.get("/api/incidents").json()) == 0
