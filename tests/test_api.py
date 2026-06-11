from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from cloud_log_pipeline.models import validate_event
from cloud_log_pipeline.storage import LogStorage



def _seed_data() -> str:
    storage = LogStorage()
    error_event = validate_event(
        {
            "event_id": str(uuid4()),
            "service": "auth-service",
            "level": "ERROR",
            "message": "Authentication failed",
            "timestamp": "2024-01-12T10:00:00Z",
            "metadata": {"user_id": "user-9", "ip": "10.0.0.8"},
        }
    )
    info_event = validate_event(
        {
            "event_id": str(uuid4()),
            "service": "auth-service",
            "level": "INFO",
            "message": "User login successful",
            "timestamp": "2024-01-13T10:00:00Z",
            "metadata": {"user_id": "user-10", "ip": "10.0.0.9"},
        }
    )
    storage.store_event(error_event)
    storage.store_event(info_event)
    return error_event.event_id



def test_health_endpoint(aws_resources) -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"



def test_logs_endpoint_filters_by_service_and_level(aws_resources) -> None:
    _seed_data()
    client = TestClient(app)

    response = client.get(
        "/logs",
        params={
            "service": "auth-service",
            "level": "ERROR",
            "from": "2024-01-01",
            "to": "2024-01-31",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["items"][0]["level"] == "ERROR"



def test_get_log_by_event_id_endpoint(aws_resources) -> None:
    event_id = _seed_data()
    client = TestClient(app)

    response = client.get(f"/logs/{event_id}")

    assert response.status_code == 200
    assert response.json()["event_id"] == event_id



def test_stats_endpoint_returns_level_counts(aws_resources) -> None:
    _seed_data()
    client = TestClient(app)

    response = client.get("/stats", params={"service": "auth-service"})

    assert response.status_code == 200
    assert response.json()["counts"] == {"INFO": 1, "WARN": 0, "ERROR": 1}
