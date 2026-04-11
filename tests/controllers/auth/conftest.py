from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.models import Company, User
from api.services.auth import hash_password
from api.services.session_store import create_session
from tests.constants import (
    DEFAULT_COMPANY_EMAIL,
    DEFAULT_COMPANY_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_USER_EMAIL,
)


@pytest.fixture(autouse=True)
def _override_db(
    app: FastAPI,
    session: AsyncSession,
) -> Generator[None, None, None]:
    async def _test_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_async_session] = _test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(session: AsyncSession) -> User:
    company = Company(
        name=DEFAULT_COMPANY_NAME,
        legal_form="LLC",
        legal_address="123 Test Street",
        contact_name="Test Contact",
        business_area="IT",
        email=DEFAULT_COMPANY_EMAIL,
    )
    session.add(company)
    await session.flush()

    user = User(
        email=DEFAULT_USER_EMAIL,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role="admin",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    return user


@pytest.fixture
async def auth_client(
    transport: ASGITransport,
    registered_user: User,
    fake_redis_client: FakeAsyncRedis,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    sid = await create_session(fake_redis_client, registered_user.id)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={"session_id": str(sid)},
    ) as c:
        yield c
