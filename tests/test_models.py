from __future__ import annotations

from uuid import uuid4

import pytest

from cloud_log_pipeline.models import ValidationError, normalize_timestamp, validate_event



def test_validate_event_accepts_valid_payload() -> None:
    payload = {
        "event_id": str(uuid4()),
        "service": "auth-service",
        "level": "INFO",
        "message": "User login successful",
        "timestamp": "2024-01-01T12:30:45-05:00",
        "metadata": {"user_id": "user-123", "ip": "127.0.0.1"},
    }

    event = validate_event(payload)

    assert event.service == "auth-service"
    assert event.timestamp == "2024-01-01T17:30:45Z"



def test_validate_event_rejects_malformed_payload() -> None:
    with pytest.raises(ValidationError):
        validate_event({"service": "auth-service"})



def test_normalize_timestamp_converts_to_utc() -> None:
    assert normalize_timestamp("2024-01-01T12:30:45-05:00") == "2024-01-01T17:30:45Z"
