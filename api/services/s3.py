from __future__ import annotations

import asyncio
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from decouple import config

S3_ENDPOINT: str = config("S3_ENDPOINT", default="http://localhost:9000")
S3_ACCESS_KEY: str = config("MINIO_ROOT_USER", default="admin")
S3_SECRET_KEY: str = config("MINIO_ROOT_PASSWORD", default="adminadmin")
S3_BUCKET: str = config("S3_BUCKET", default="stafftracker")


@lru_cache
def _get_client():  # noqa: ANN202
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )


def ensure_bucket() -> None:
    client = _get_client()
    try:
        client.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=S3_BUCKET)


async def upload(key: str, data: bytes, content_type: str) -> None:
    client = _get_client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


async def download(key: str) -> tuple[bytes, str]:
    client = _get_client()
    response = await asyncio.to_thread(
        client.get_object,
        Bucket=S3_BUCKET,
        Key=key,
    )
    body: bytes = response["Body"].read()
    content_type: str = response.get("ContentType", "application/octet-stream")
    return body, content_type


async def delete(key: str) -> None:
    client = _get_client()
    await asyncio.to_thread(
        client.delete_object,
        Bucket=S3_BUCKET,
        Key=key,
    )
