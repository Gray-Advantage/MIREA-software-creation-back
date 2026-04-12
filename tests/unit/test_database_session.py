import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session


@pytest.mark.asyncio
async def test_get_async_session_yields_async_session() -> None:
    async for session in get_async_session():
        assert isinstance(session, AsyncSession)
        break
