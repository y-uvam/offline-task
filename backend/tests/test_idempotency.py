import threading
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


def _make_incident(client_id: str = "idem-001"):
    return {
        "client_id": client_id,
        "title": "Idempotency test incident",
        "created_at": "2026-09-19T12:00:00Z",
    }


class TestBasicIdempotency:
    def test_duplicate_post_returns_same_record(self, client):
        first = client.post("/api/incidents", json=_make_incident()).json()
        second = client.post("/api/incidents", json=_make_incident()).json()

        assert first["server_id"] == second["server_id"]
        assert first["was_duplicate"] is False
        assert second["was_duplicate"] is True

    def test_duplicate_post_does_not_increase_count(self, client):
        client.post("/api/incidents", json=_make_incident())
        client.post("/api/incidents", json=_make_incident())
        client.post("/api/incidents", json=_make_incident())

        incidents = client.get("/api/incidents").json()
        assert len(incidents) == 1

    def test_different_client_ids_create_separate_incidents(self, client):
        client.post("/api/incidents", json=_make_incident("a"))
        client.post("/api/incidents", json=_make_incident("b"))

        incidents = client.get("/api/incidents").json()
        assert len(incidents) == 2


class TestConcurrentIdempotency:
    def test_10_concurrent_posts_same_id_create_exactly_one(self, client):
        results = []
        errors = []

        def send():
            try:
                resp = client.post("/api/incidents", json=_make_incident("concurrent-001"))
                results.append(resp.json())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Unexpected errors: {errors}"

        incidents = client.get("/api/incidents").json()
        assert len(incidents) == 1

        server_ids = {r["server_id"] for r in results}
        assert len(server_ids) == 1

        originals = [r for r in results if not r["was_duplicate"]]
        duplicates = [r for r in results if r["was_duplicate"]]
        assert len(originals) == 1
        assert len(duplicates) == 9


class TestBenchmarkIdempotency:
    def test_10_incidents_each_sent_twice_stores_10(self, client):
        for i in range(10):
            cid = f"bench-{i:03d}"
            client.post("/api/incidents", json=_make_incident(cid))
            client.post("/api/incidents", json=_make_incident(cid))

        incidents = client.get("/api/incidents").json()
        assert len(incidents) == 10

        ids = [inc["client_id"] for inc in incidents]
        assert ids == [f"bench-{i:03d}" for i in range(10)]
