from __future__ import annotations

import asyncio
import json
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from decouple import config

S3_ENDPOINT: str = config("S3_ENDPOINT", default="http://minio:9000")
S3_PUBLIC_URL: str = config("S3_PUBLIC_URL", default="http://localhost:9000")
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


def public_url(key: str) -> str:
    return f"{S3_PUBLIC_URL}/{S3_BUCKET}/{key}"


def extract_key(url_or_key: str) -> str:
    prefix = f"{S3_PUBLIC_URL}/{S3_BUCKET}/"
    if url_or_key.startswith(prefix):
        return url_or_key[len(prefix) :]
    return url_or_key


def _public_read_policy() -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{S3_BUCKET}/*"],
                },
            ],
        },
    )


def ensure_bucket() -> None:
    client = _get_client()
    try:
        client.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=S3_BUCKET)
    client.put_bucket_policy(Bucket=S3_BUCKET, Policy=_public_read_policy())


async def upload(key: str, data: bytes, content_type: str) -> None:
    client = _get_client()
    await asyncio.to_thread(
        client.put_object,
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


async def delete(key: str) -> None:
    client = _get_client()
    await asyncio.to_thread(
        client.delete_object,
        Bucket=S3_BUCKET,
        Key=key,
    )
