"""Smoke test for the health endpoint. Template for future endpoint tests."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
