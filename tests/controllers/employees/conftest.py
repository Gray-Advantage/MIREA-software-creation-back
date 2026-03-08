from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.models import ApiSession, Company, EmployeeProfile, User
from api.services.auth import hash_password
from tests.constants import (
    DEFAULT_COMPANY_EMAIL,
    DEFAULT_COMPANY_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_USER_EMAIL,
)

SESSION_TTL_DAYS = 30

EMPLOYEE_EMAIL = "employee@test.com"
EMPLOYEE_PASSWORD = "employeepass123"

EMPLOYEE_PAYLOAD: dict[str, Any] = {
    "email": EMPLOYEE_EMAIL,
    "full_name": "Тестовый Сотрудник",
    "phone": "+79991234567",
    "position": "Разработчик",
    "rate_type": "hourly",
    "rate_amount": "500.00",
    "currency": "RUB",
}


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
async def registered_admin(session: AsyncSession, company: Company) -> User:
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
    session: AsyncSession,
    registered_admin: User,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    api_session = ApiSession(
        user_id=registered_admin.id,
        expires_at=datetime.now(UTC) + timedelta(days=SESSION_TTL_DAYS),
    )
    session.add(api_session)
    await session.flush()

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={"session_id": str(api_session.id)},
    ) as c:
        yield c


@pytest.fixture
async def employee_user(
    session: AsyncSession,
    company: Company,
) -> User:
    user = User(
        email=EMPLOYEE_EMAIL,
        password_hash=hash_password(EMPLOYEE_PASSWORD),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Тестовый Сотрудник",
        phone="+79991234567",
        position="Разработчик",
        rate_type="hourly",
        rate_amount=Decimal("500.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    return user


@pytest.fixture
async def other_company_employee(session: AsyncSession) -> User:
    other_company = Company(
        name="Other Company",
        legal_form="LLC",
        legal_address="456 Other Street",
        contact_name="Other Contact",
        business_area="Retail",
        email="other@company.com",
    )
    session.add(other_company)
    await session.flush()

    user = User(
        email="other_employee@test.com",
        password_hash=hash_password("otherpass123"),
        role="employee",
        company_id=other_company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Другой Сотрудник",
        position="Менеджер",
        rate_type="daily",
        rate_amount=Decimal("3000.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    return user
