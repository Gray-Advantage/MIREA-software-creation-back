from collections.abc import AsyncGenerator

from decouple import config
from redis.asyncio import Redis, from_url

_redis_slot: list[Redis | None] = [None]


def redis_url() -> str:
    return config("REDIS_URL", default="redis://localhost:6379/0")


async def init_redis() -> None:
    if config("ENVIRONMENT", default="") == "pytest":
        return
    if _redis_slot[0] is None:
        _redis_slot[0] = from_url(redis_url(), decode_responses=True)


async def shutdown_redis() -> None:
    if _redis_slot[0] is not None:
        await _redis_slot[0].aclose()
        _redis_slot[0] = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    if _redis_slot[0] is None:
        msg = "Redis client is not initialized"
        raise RuntimeError(msg)
    yield _redis_slot[0]
