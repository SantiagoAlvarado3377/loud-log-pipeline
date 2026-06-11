from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws

from api.main import get_storage
from cloud_log_pipeline.config import get_settings


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/log-ingestion-queue")
    monkeypatch.setenv("S3_BUCKET", "log-archive")
    monkeypatch.setenv("DYNAMODB_TABLE", "log-index")
    monkeypatch.setenv("DLQ_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/log-dlq")
    get_settings.cache_clear()
    get_storage.cache_clear()
    yield
    get_settings.cache_clear()
    get_storage.cache_clear()


@pytest.fixture
def aws_resources():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")

        s3.create_bucket(Bucket=os.environ["S3_BUCKET"])
        dynamodb.create_table(
            TableName=os.environ["DYNAMODB_TABLE"],
            AttributeDefinitions=[
                {"AttributeName": "service", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "service", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        sqs.create_queue(QueueName="log-dlq")
        sqs.create_queue(QueueName="log-ingestion-queue")

        yield {"s3": s3, "dynamodb": dynamodb, "sqs": sqs}
