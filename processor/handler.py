from __future__ import annotations

import json
from typing import Any

from cloud_log_pipeline.aws import get_boto3_client
from cloud_log_pipeline.config import get_settings
from cloud_log_pipeline.models import ValidationError, validate_event
from cloud_log_pipeline.storage import LogStorage



def _send_to_dlq(body: str, reason: str) -> None:
    settings = get_settings()
    sqs_client = get_boto3_client("sqs")
    sqs_client.send_message(
        QueueUrl=settings.dlq_url,
        MessageBody=json.dumps({"reason": reason, "body": body}),
    )



def process_record(record: dict[str, Any], storage: LogStorage) -> bool:
    body = record.get("body", "")
    try:
        payload = json.loads(body)
        event = validate_event(payload)
        storage.store_event(event)
        return True
    except (json.JSONDecodeError, ValidationError) as exc:
        _send_to_dlq(body, str(exc))
        return False



def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, int]:
    storage = LogStorage()
    processed = 0
    failed = 0
    for record in event.get("Records", []):
        if process_record(record, storage):
            processed += 1
        else:
            failed += 1
    return {"processed": processed, "failed": failed}
