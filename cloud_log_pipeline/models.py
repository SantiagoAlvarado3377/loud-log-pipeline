from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time
from uuid import UUID

ALLOWED_SERVICES = {"auth-service", "billing-service", "notification-service"}
ALLOWED_LEVELS = {"INFO", "WARN", "ERROR"}


class ValidationError(ValueError):
    """Raised when an event does not match the expected schema."""


@dataclass(frozen=True)
class LogEvent:
    event_id: str
    service: str
    level: str
    message: str
    timestamp: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)



def _parse_datetime(value: str) -> datetime:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValidationError("timestamp must be ISO-8601 formatted") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)



def normalize_timestamp(value: str) -> str:
    return _parse_datetime(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")



def coerce_query_timestamp(value: str, *, end_of_day: bool = False) -> str:
    if len(value) == 10:
        parsed_date = date.fromisoformat(value)
        parsed_time = time.max if end_of_day else time.min
        combined = datetime.combine(parsed_date, parsed_time, tzinfo=UTC)
        return combined.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return normalize_timestamp(value)



def validate_event(payload: dict) -> LogEvent:
    required_fields = {"event_id", "service", "level", "message", "timestamp", "metadata"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValidationError(f"missing required fields: {', '.join(sorted(missing))}")

    try:
        UUID(str(payload["event_id"]))
    except (ValueError, TypeError) as exc:
        raise ValidationError("event_id must be a valid UUID") from exc

    service = payload["service"]
    if service not in ALLOWED_SERVICES:
        raise ValidationError(f"service must be one of {sorted(ALLOWED_SERVICES)}")

    level = payload["level"]
    if level not in ALLOWED_LEVELS:
        raise ValidationError(f"level must be one of {sorted(ALLOWED_LEVELS)}")

    message = payload["message"]
    if not isinstance(message, str) or not message.strip():
        raise ValidationError("message must be a non-empty string")

    metadata = payload["metadata"]
    if not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object")

    return LogEvent(
        event_id=str(payload["event_id"]),
        service=service,
        level=level,
        message=message.strip(),
        timestamp=normalize_timestamp(str(payload["timestamp"])),
        metadata=metadata,
    )
