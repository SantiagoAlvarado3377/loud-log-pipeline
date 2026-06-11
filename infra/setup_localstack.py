from __future__ import annotations

import json

from botocore.exceptions import ClientError

from cloud_log_pipeline.aws import get_boto3_client
from cloud_log_pipeline.config import get_settings



def ensure_bucket(bucket_name: str) -> None:
    s3 = get_boto3_client("s3")
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        s3.create_bucket(Bucket=bucket_name)



def ensure_table(table_name: str) -> None:
    dynamodb = get_boto3_client("dynamodb")
    existing_tables = dynamodb.list_tables()["TableNames"]
    if table_name in existing_tables:
        return
    dynamodb.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "service", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
            {"AttributeName": "event_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "service", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "event-id-index",
                "KeySchema": [{"AttributeName": "event_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.get_waiter("table_exists").wait(TableName=table_name)



def ensure_queues() -> None:
    settings = get_settings()
    sqs = get_boto3_client("sqs")
    dlq_name = settings.dlq_url.rstrip("/").split("/")[-1]
    queue_name = settings.sqs_queue_url.rstrip("/").split("/")[-1]

    dlq_url = sqs.create_queue(QueueName=dlq_name)["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    sqs.create_queue(
        QueueName=queue_name,
        Attributes={
            "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "1"})
        },
    )


if __name__ == "__main__":
    settings = get_settings()
    ensure_queues()
    ensure_bucket(settings.s3_bucket)
    ensure_table(settings.dynamodb_table)
    print("LocalStack resources are ready")
