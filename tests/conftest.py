from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from api.database import DATABASE_URL
from api.main import app as fastapi_app


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return fastapi_app


@pytest.fixture(scope="session")
def transport(app: FastAPI) -> ASGITransport:
    return ASGITransport(app=app)


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(DATABASE_URL, echo=False)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as conn:
        trans = await conn.begin()
        nested = await conn.begin_nested()

        async_session = AsyncSession(bind=conn, expire_on_commit=False)

        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def restart_savepoint(
            _session: Any,
            _transaction: Any,
        ) -> None:
            nonlocal nested
            if not nested.is_active:
                nested = conn.sync_connection.begin_nested()

        yield async_session

        await async_session.close()
        await trans.rollback()


@pytest.fixture
async def client(
    transport: ASGITransport,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as c:
        yield c
