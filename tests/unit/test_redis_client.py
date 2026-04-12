from unittest.mock import patch

import pytest
from fakeredis import FakeAsyncRedis

from api import redis_client


@pytest.fixture(autouse=True)
def clear_redis_slot() -> None:
    redis_client._redis_slot[0] = None
    yield
    redis_client._redis_slot[0] = None


@pytest.mark.asyncio
async def test_init_redis_skips_in_pytest_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "pytest")
    await redis_client.init_redis()
    assert redis_client._redis_slot[0] is None


@pytest.mark.asyncio
async def test_init_shutdown_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    fake = FakeAsyncRedis(decode_responses=True)
    with patch.object(redis_client, "from_url", return_value=fake):
        await redis_client.init_redis()
    assert redis_client._redis_slot[0] is fake

    await redis_client.shutdown_redis()
    assert redis_client._redis_slot[0] is None


@pytest.mark.asyncio
async def test_init_redis_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    fake = FakeAsyncRedis(decode_responses=True)
    with patch.object(redis_client, "from_url", return_value=fake):
        await redis_client.init_redis()
        await redis_client.init_redis()
    assert redis_client._redis_slot[0] is fake
    await redis_client.shutdown_redis()


@pytest.mark.asyncio
async def test_get_redis_raises_when_not_initialized() -> None:
    gen = redis_client.get_redis()
    with pytest.raises(RuntimeError, match="not initialized"):
        await gen.__anext__()


@pytest.mark.asyncio
async def test_get_redis_yields_initialized_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    fake = FakeAsyncRedis(decode_responses=True)
    with patch.object(redis_client, "from_url", return_value=fake):
        await redis_client.init_redis()

    gen = redis_client.get_redis()
    assert await gen.__anext__() is fake
