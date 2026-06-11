from __future__ import annotations

import boto3

from cloud_log_pipeline.config import get_settings



def get_boto3_client(service_name: str):
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client(service_name, **kwargs)



def get_dynamodb_resource():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.resource("dynamodb", **kwargs)
