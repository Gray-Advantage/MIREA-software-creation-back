from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

import api.services.s3 as s3_module


@pytest.fixture(autouse=True)
def clear_s3_client_cache() -> None:
    s3_module._get_client.cache_clear()
    yield
    s3_module._get_client.cache_clear()


def test_get_client_returns_boto3_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    monkeypatch.setattr(
        s3_module.boto3,
        "client",
        lambda *_a, **_k: fake,
    )
    s3_module._get_client.cache_clear()
    assert s3_module._get_client() is fake
    s3_module._get_client.cache_clear()


def test_public_url() -> None:
    url = s3_module.public_url("avatars/x.png")
    assert url.endswith("/stafftracker/avatars/x.png")


def test_extract_key_strips_public_prefix() -> None:
    prefix = "http://localhost:9000/stafftracker/"
    assert s3_module.extract_key(f"{prefix}key/z.png") == "key/z.png"


def test_extract_key_returns_as_is_without_prefix() -> None:
    assert s3_module.extract_key("raw-key") == "raw-key"


def test_ensure_bucket_when_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    monkeypatch.setattr(s3_module, "_get_client", lambda: client)

    s3_module.ensure_bucket()

    client.head_bucket.assert_called_once_with(Bucket="stafftracker")
    client.create_bucket.assert_not_called()
    client.put_bucket_policy.assert_called_once()


def test_ensure_bucket_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadBucket",
    )
    monkeypatch.setattr(s3_module, "_get_client", lambda: client)

    s3_module.ensure_bucket()

    client.create_bucket.assert_called_once_with(Bucket="stafftracker")


@pytest.mark.asyncio
async def test_upload_delegates_to_put_object(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    monkeypatch.setattr(s3_module, "_get_client", lambda: client)

    await s3_module.upload("k", b"data", "image/png")

    client.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_delete_delegates_to_delete_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    monkeypatch.setattr(s3_module, "_get_client", lambda: client)

    await s3_module.delete("k")

    client.delete_object.assert_called_once()
