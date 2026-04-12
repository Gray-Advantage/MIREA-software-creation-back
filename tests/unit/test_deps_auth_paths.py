import uuid
from collections.abc import AsyncGenerator
from http import HTTPStatus

import httpx
import pytest
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.main import app
from api.models import Company, User
from api.redis_client import get_redis
from api.services.auth import hash_password
from api.services.session_store import create_session


@pytest.fixture
async def api_with_session(
    session: AsyncSession,
    fake_redis_client: FakeAsyncRedis,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def _db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    async def _redis() -> AsyncGenerator[FakeAsyncRedis, None]:
        yield fake_redis_client

    app.dependency_overrides[get_async_session] = _db
    app.dependency_overrides[get_redis] = _redis

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.pop(get_async_session, None)
    app.dependency_overrides.pop(get_redis, None)


@pytest.mark.asyncio
async def test_current_user_rejects_invalid_uuid_cookie(
    api_with_session: httpx.AsyncClient,
) -> None:
    r = await api_with_session.get(
        "/api/auth/me",
        cookies={"session_id": "not-a-uuid"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_current_user_rejects_expired_redis_session(
    api_with_session: httpx.AsyncClient,
    session: AsyncSession,
) -> None:
    company = Company(
        name="C",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="cdeps@t.com",
    )
    session.add(company)
    await session.flush()
    user = User(
        email="udeps@t.com",
        password_hash=hash_password("p"),
        role="admin",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    sid = uuid.uuid4()
    r = await api_with_session.get(
        "/api/auth/me",
        cookies={"session_id": str(sid)},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_current_user_rejects_missing_user_row(
    api_with_session: httpx.AsyncClient,
    fake_redis_client: FakeAsyncRedis,
) -> None:
    sid = await create_session(fake_redis_client, 999999999)
    r = await api_with_session.get(
        "/api/auth/me",
        cookies={"session_id": str(sid)},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_current_user_rejects_inactive_user(
    api_with_session: httpx.AsyncClient,
    session: AsyncSession,
    fake_redis_client: FakeAsyncRedis,
) -> None:
    company = Company(
        name="C2",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="cdeps2@t.com",
    )
    session.add(company)
    await session.flush()
    user = User(
        email="inactive@t.com",
        password_hash=hash_password("p"),
        role="admin",
        company_id=company.id,
        is_active=False,
    )
    session.add(user)
    await session.flush()

    sid = await create_session(fake_redis_client, user.id)
    r = await api_with_session.get(
        "/api/auth/me",
        cookies={"session_id": str(sid)},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_require_admin_forbidden_for_employee(
    api_with_session: httpx.AsyncClient,
    session: AsyncSession,
    fake_redis_client: FakeAsyncRedis,
) -> None:
    company = Company(
        name="C3",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="cdeps3@t.com",
    )
    session.add(company)
    await session.flush()
    user = User(
        email="empdeps@t.com",
        password_hash=hash_password("p"),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    sid = await create_session(fake_redis_client, user.id)
    r = await api_with_session.get(
        "/api/company",
        cookies={"session_id": str(sid)},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_require_employee_forbidden_for_admin(
    api_with_session: httpx.AsyncClient,
    session: AsyncSession,
    fake_redis_client: FakeAsyncRedis,
) -> None:
    company = Company(
        name="C4",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="cdeps4@t.com",
    )
    session.add(company)
    await session.flush()
    user = User(
        email="admdeps@t.com",
        password_hash=hash_password("p"),
        role="admin",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    sid = await create_session(fake_redis_client, user.id)
    r = await api_with_session.get(
        "/api/me/profile",
        cookies={"session_id": str(sid)},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN
