import uuid
from uuid import UUID

from redis.asyncio import Redis

SESSION_TTL_DAYS = 30
SESSION_TTL_SECONDS = SESSION_TTL_DAYS * 86400
_SESSION_PREFIX = "st:sess:"


def _session_key(session_id: UUID) -> str:
    return f"{_SESSION_PREFIX}{session_id}"


async def create_session(redis: Redis, user_id: int) -> UUID:
    session_id = uuid.uuid4()
    await redis.set(
        _session_key(session_id),
        str(user_id),
        ex=SESSION_TTL_SECONDS,
    )
    return session_id


async def get_user_id(redis: Redis, session_id: UUID) -> int | None:
    raw = await redis.get(_session_key(session_id))
    if raw is None:
        return None
    return int(raw)


async def delete_session_for_user(
    redis: Redis,
    session_id: UUID,
    user_id: int,
) -> None:
    key = _session_key(session_id)
    current = await redis.get(key)
    if current is not None and int(current) == user_id:
        await redis.delete(key)


async def delete_all_sessions_for_user(redis: Redis, user_id: int) -> None:
    uid = str(user_id)
    async for key in redis.scan_iter(match=f"{_SESSION_PREFIX}*", count=256):
        val = await redis.get(key)
        if val == uid:
            await redis.delete(key)
