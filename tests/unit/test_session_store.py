import uuid

import pytest
from fakeredis import FakeAsyncRedis

from api.services.session_store import (
    create_session,
    delete_all_sessions_for_user,
    delete_session_for_user,
    get_user_id,
)


@pytest.fixture
def redis() -> FakeAsyncRedis:
    return FakeAsyncRedis(decode_responses=True)


@pytest.mark.asyncio
async def test_get_user_id_returns_none_when_missing(redis: FakeAsyncRedis) -> None:
    assert await get_user_id(redis, uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_get_user_id_returns_user_id(redis: FakeAsyncRedis) -> None:
    uid = 42
    sid = await create_session(redis, uid)
    assert await get_user_id(redis, sid) == uid


@pytest.mark.asyncio
async def test_delete_session_for_user_removes_key(redis: FakeAsyncRedis) -> None:
    sid = await create_session(redis, 1)
    await delete_session_for_user(redis, sid, 1)
    assert await get_user_id(redis, sid) is None


@pytest.mark.asyncio
async def test_delete_session_for_user_wrong_user_noop(
    redis: FakeAsyncRedis,
) -> None:
    sid = await create_session(redis, 1)
    await delete_session_for_user(redis, sid, 999)
    assert await get_user_id(redis, sid) == 1


@pytest.mark.asyncio
async def test_delete_all_sessions_for_user_only_matching(
    redis: FakeAsyncRedis,
) -> None:
    target_uid = 7
    other_uid = 8
    s_a = await create_session(redis, target_uid)
    s_b = await create_session(redis, target_uid)
    s_other = await create_session(redis, other_uid)

    await delete_all_sessions_for_user(redis, target_uid)

    assert await get_user_id(redis, s_a) is None
    assert await get_user_id(redis, s_b) is None
    assert await get_user_id(redis, s_other) == other_uid
