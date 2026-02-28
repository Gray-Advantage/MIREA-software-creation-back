from collections.abc import AsyncGenerator
from urllib.parse import quote_plus

from decouple import config
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_PG_USER = config("POSTGRES_USER", default="stafftracker")
_PG_PASSWORD = config("POSTGRES_PASSWORD", default="stafftracker")
_PG_HOST = config("POSTGRES_HOST", default="localhost")
_PG_PORT = config("POSTGRES_PORT", default="5432")
_PG_DB = config("POSTGRES_DB", default="stafftracker")

DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{quote_plus(_PG_USER)}:{quote_plus(_PG_PASSWORD)}"
    f"@{_PG_HOST}:{_PG_PORT}/{_PG_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
