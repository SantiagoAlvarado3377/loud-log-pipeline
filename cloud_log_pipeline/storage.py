from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any

from boto3.dynamodb.conditions import Attr, Key

from cloud_log_pipeline.aws import get_boto3_client, get_dynamodb_resource
from cloud_log_pipeline.config import get_settings
from cloud_log_pipeline.models import LogEvent


class LogStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.s3_client = get_boto3_client("s3")
        self.dynamodb_resource = get_dynamodb_resource()
        self.table = self.dynamodb_resource.Table(settings.dynamodb_table)

    def archive_event(self, event: LogEvent) -> str:
        event_dt = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        s3_key = (
            f"logs/{event.service}/{event_dt:%Y}/{event_dt:%m}/{event_dt:%d}/{event.event_id}.json"
        )
        self.s3_client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=s3_key,
            Body=json.dumps(event.to_dict()).encode("utf-8"),
            ContentType="application/json",
        )
        return s3_key

    def index_event(self, event: LogEvent, s3_key: str) -> dict[str, Any]:
        item = {
            "service": event.service,
            "timestamp": event.timestamp,
            "event_id": event.event_id,
            "level": event.level,
            "message": event.message,
            "s3_key": s3_key,
        }
        self.table.put_item(Item=item)
        return item

    def store_event(self, event: LogEvent) -> dict[str, Any]:
        s3_key = self.archive_event(event)
        return self.index_event(event, s3_key)

    def query_logs(
        self,
        *,
        service: str,
        level: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> list[dict[str, Any]]:
        key_condition = Key("service").eq(service)
        if from_timestamp and to_timestamp:
            key_condition &= Key("timestamp").between(from_timestamp, to_timestamp)
        elif from_timestamp:
            key_condition &= Key("timestamp").gte(from_timestamp)
        elif to_timestamp:
            key_condition &= Key("timestamp").lte(to_timestamp)

        query_kwargs: dict[str, Any] = {"KeyConditionExpression": key_condition}
        if level:
            query_kwargs["FilterExpression"] = Attr("level").eq(level)

        response = self.table.query(**query_kwargs)
        return sorted(response.get("Items", []), key=lambda item: item["timestamp"])

    def get_log_by_event_id(self, event_id: str) -> dict[str, Any] | None:
        response = self.table.scan(FilterExpression=Attr("event_id").eq(event_id))
        items = response.get("Items", [])
        if not items:
            return None
        item = items[0]
        body = self.s3_client.get_object(Bucket=self.settings.s3_bucket, Key=item["s3_key"])[
            "Body"
        ].read()
        return json.loads(body)

    def get_stats(self, service: str) -> dict[str, int]:
        response = self.table.query(KeyConditionExpression=Key("service").eq(service))
        counts = Counter(item["level"] for item in response.get("Items", []))
        return {level: counts.get(level, 0) for level in ["INFO", "WARN", "ERROR"]}

    def health_check(self) -> dict[str, str]:
        checks = {"dynamodb": "ok", "s3": "ok"}
        try:
            self.table.load()
        except Exception:
            checks["dynamodb"] = "error"
        try:
            self.s3_client.head_bucket(Bucket=self.settings.s3_bucket)
        except Exception:
            checks["s3"] = "error"
        return checks
