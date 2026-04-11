from collections.abc import AsyncGenerator

from decouple import config
from redis.asyncio import Redis, from_url

_redis: Redis | None = None


def redis_url() -> str:
    return config("REDIS_URL", default="redis://localhost:6379/0")


async def init_redis() -> None:
    global _redis
    if config("ENVIRONMENT", default="") == "pytest":
        return
    if _redis is None:
        _redis = from_url(redis_url(), decode_responses=True)


async def shutdown_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    if _redis is None:
        msg = "Redis client is not initialized"
        raise RuntimeError(msg)
    yield _redis
