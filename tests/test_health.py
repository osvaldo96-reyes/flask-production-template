from unittest.mock import patch


def test_liveness(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_readiness_ok(client):
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.get_json()["database"] == "ok"


def test_readiness_db_down(client):
    with patch("app.health.db.session.execute", side_effect=ConnectionError("db down")):
        resp = client.get("/readyz")
    assert resp.status_code == 503
    assert resp.get_json()["status"] == "unavailable"


def test_metrics_exposed(client):
    client.get("/healthz")
    body = client.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in body
    assert 'endpoint="/healthz"' in body


def test_request_id_propagated(client):
    resp = client.get("/healthz", headers={"X-Request-ID": "abc123"})
    assert resp.headers["X-Request-ID"] == "abc123"
