import pytest

from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "DATABASE", str(tmp_path / "test.db"))
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_tasks(client):
    assert client.get("/tasks").json == []
    created = client.post("/tasks", json={"title": "Tester la CI"})
    assert created.status_code == 201
    assert client.get("/tasks").json == [created.json]


def test_invalid_title(client):
    assert client.post("/tasks", json={"title": " "}).status_code == 400


def test_metrics(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert 'http_request_duration_seconds_bucket{le="0.3",route="/health",status="200"}' in body
