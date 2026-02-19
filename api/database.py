from collections.abc import AsyncGenerator

from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql+asyncpg://stafftracker:stafftracker@localhost:5432/stafftracker",
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
