from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    aws_endpoint_url: str | None
    aws_region: str
    sqs_queue_url: str
    s3_bucket: str
    dynamodb_table: str
    dlq_url: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    endpoint = os.getenv("AWS_ENDPOINT_URL") or None
    return Settings(
        aws_endpoint_url=endpoint,
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        sqs_queue_url=os.getenv(
            "SQS_QUEUE_URL",
            "http://localhost:4566/000000000000/log-ingestion-queue",
        ),
        s3_bucket=os.getenv("S3_BUCKET", "log-archive"),
        dynamodb_table=os.getenv("DYNAMODB_TABLE", "log-index"),
        dlq_url=os.getenv("DLQ_URL", "http://localhost:4566/000000000000/log-dlq"),
    )
