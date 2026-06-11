from __future__ import annotations

import json

from cloud_log_pipeline.aws import get_boto3_client
from cloud_log_pipeline.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    sqs_client = get_boto3_client("sqs")
    response = sqs_client.receive_message(
        QueueUrl=settings.dlq_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=1,
    )
    for message in response.get("Messages", []):
        payload = json.loads(message["Body"])
        print(json.dumps(payload, indent=2))
