from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cloud_log_pipeline.aws import get_boto3_client
from cloud_log_pipeline.config import get_settings

SERVICE_TEMPLATES = {
    "auth-service": [
        ("INFO", "User login successful", {"action": "login", "status": "success"}),
        ("WARN", "Token refresh retried", {"action": "token-refresh", "status": "retry"}),
        ("ERROR", "Authentication failed", {"action": "login", "status": "failure"}),
    ],
    "billing-service": [
        ("INFO", "Payment processed", {"action": "payment", "status": "success"}),
        ("WARN", "Subscription updated", {"action": "subscription", "status": "changed"}),
        ("ERROR", "Payment authorization failed", {"action": "payment", "status": "failure"}),
    ],
    "notification-service": [
        ("INFO", "Notification sent", {"action": "delivery", "channel": "email"}),
        ("WARN", "Notification retry scheduled", {"action": "retry", "channel": "sms"}),
        ("ERROR", "Notification delivery failed", {"action": "delivery", "status": "failure"}),
    ],
}


def build_random_event(service: str) -> dict:
    level, message, metadata = random.choice(SERVICE_TEMPLATES[service])
    event_time = datetime.now(UTC) - timedelta(minutes=random.randint(0, 120))
    enriched_metadata = {
        **metadata,
        "user_id": f"user-{random.randint(1000, 9999)}",
        "ip": f"192.168.1.{random.randint(1, 254)}",
    }
    return {
        "event_id": str(uuid4()),
        "service": service,
        "level": level,
        "message": message,
        "timestamp": event_time.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "metadata": enriched_metadata,
    }



def emit_events(service: str, count: int | None = None) -> list[dict]:
    settings = get_settings()
    sqs_client = get_boto3_client("sqs")
    event_count = count if count is not None else random.randint(10, 50)
    events = [build_random_event(service) for _ in range(event_count)]
    for event in events:
        sqs_client.send_message(QueueUrl=settings.sqs_queue_url, MessageBody=json.dumps(event))
    return events
