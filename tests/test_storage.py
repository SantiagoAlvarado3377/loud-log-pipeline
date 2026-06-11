from __future__ import annotations

from uuid import uuid4

from cloud_log_pipeline.models import validate_event
from cloud_log_pipeline.storage import LogStorage



def _sample_event(service: str = "auth-service", level: str = "INFO", timestamp: str = "2024-01-01T12:00:00Z"):
    return validate_event(
        {
            "event_id": str(uuid4()),
            "service": service,
            "level": level,
            "message": f"{service} event",
            "timestamp": timestamp,
            "metadata": {"user_id": "user-1", "ip": "127.0.0.1"},
        }
    )



def test_store_and_query_logs(aws_resources) -> None:
    storage = LogStorage()
    storage.store_event(_sample_event(level="ERROR", timestamp="2024-01-05T12:00:00Z"))
    storage.store_event(_sample_event(level="INFO", timestamp="2024-01-06T12:00:00Z"))

    results = storage.query_logs(
        service="auth-service",
        level="ERROR",
        from_timestamp="2024-01-01T00:00:00Z",
        to_timestamp="2024-01-31T23:59:59Z",
    )

    assert len(results) == 1
    assert results[0]["level"] == "ERROR"
    assert results[0]["s3_key"].startswith("logs/auth-service/2024/01/05/")



def test_fetch_full_event_from_s3(aws_resources) -> None:
    storage = LogStorage()
    event = _sample_event(service="billing-service", level="WARN")
    storage.store_event(event)

    fetched = storage.get_log_by_event_id(event.event_id)

    assert fetched == event.to_dict()
