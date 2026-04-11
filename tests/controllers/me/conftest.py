import datetime as _dt
from collections.abc import AsyncGenerator, Generator
from decimal import Decimal

import httpx
import pytest
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.models import (
    Adjustment,
    Company,
    EmployeeProfile,
    Schedule,
    User,
)
from api.services.auth import hash_password
from api.services.session_store import create_session
from tests.constants import (
    DEFAULT_COMPANY_EMAIL,
    DEFAULT_COMPANY_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_USER_EMAIL,
)

EMPLOYEE_EMAIL = "worker@test.com"


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
async def company(session: AsyncSession) -> Company:
    obj = Company(
        name=DEFAULT_COMPANY_NAME,
        legal_form="LLC",
        legal_address="123 Test Street",
        contact_name="Test Contact",
        business_area="IT",
        email=DEFAULT_COMPANY_EMAIL,
    )
    session.add(obj)
    await session.flush()
    return obj


@pytest.fixture
async def employee_user(
    session: AsyncSession,
    company: Company,
) -> tuple[User, EmployeeProfile]:
    user = User(
        email=EMPLOYEE_EMAIL,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Петров Пётр",
        phone="+79991234567",
        position="Бариста",
        rate_type="hourly",
        rate_amount=Decimal("500.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    today = _dt.datetime.now(_dt.UTC).date()
    base = today.replace(day=1)
    for i in range(3):
        session.add(
            Schedule(
                employee_id=profile.id,
                date=base + _dt.timedelta(days=i),
                start_time=_dt.time(10, 0),
                end_time=_dt.time(18, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )

    session.add(
        Adjustment(
            employee_id=profile.id,
            type="bonus",
            amount=Decimal("1000.00"),
            comment="Премия",
            date=base,
        ),
    )
    session.add(
        Adjustment(
            employee_id=profile.id,
            type="fine",
            amount=Decimal("200.00"),
            comment="Штраф",
            date=base,
        ),
    )
    await session.flush()
    return user, profile


@pytest.fixture
async def employee_client(
    transport: ASGITransport,
    employee_user: tuple[User, EmployeeProfile],
    fake_redis_client: FakeAsyncRedis,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    user, _ = employee_user
    sid = await create_session(fake_redis_client, user.id)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={"session_id": str(sid)},
    ) as c:
        yield c


@pytest.fixture
async def admin_client(
    transport: ASGITransport,
    session: AsyncSession,
    company: Company,
    fake_redis_client: FakeAsyncRedis,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    admin = User(
        email=DEFAULT_USER_EMAIL,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role="admin",
        company_id=company.id,
    )
    session.add(admin)
    await session.flush()

    sid = await create_session(fake_redis_client, admin.id)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={"session_id": str(sid)},
    ) as c:
        yield c
