import datetime as _dt
import uuid
from http import HTTPStatus
from unittest.mock import ANY

import httpx
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Company, EmployeeProfile, User
from api.services.auth import hash_password
from api.services.session_store import create_session
from tests.base import TestView


class TestMyProfile(TestView):
    URL = "/api/me/profile"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_error__admin_forbidden(
        self,
        admin_client: AsyncClient,
    ) -> None:
        response = await self.request(admin_client)
        assert response.status_code == HTTPStatus.FORBIDDEN

    async def test_success(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(employee_client)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["full_name"] == "Петров Пётр"
        assert data["position"] == "Бариста"
        assert data["currency"] == "RUB"

    async def test_success__with_avatar_url(
        self,
        employee_client: AsyncClient,
        session: AsyncSession,
        employee_user: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_user
        profile.avatar_key = "avatars/me.png"
        await session.flush()

        response = await self.request(employee_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json()["avatar_url"] is not None


class TestMySchedule(TestView):
    URL = "/api/me/schedule"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_error__admin_forbidden(
        self,
        admin_client: AsyncClient,
    ) -> None:
        response = await self.request(admin_client)
        assert response.status_code == HTTPStatus.FORBIDDEN

    async def test_success__all(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(employee_client)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) >= 3  # noqa: PLR2004

    async def test_success__by_month(
        self,
        employee_client: AsyncClient,
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(employee_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) >= 3  # noqa: PLR2004
        for entry in data:
            assert entry["date"].startswith(month)

    async def test_success__empty_month(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(
            employee_client,
            params={"month": "2020-01"},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []


class TestMySalary(TestView):
    URL = "/api/me/salary"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, params={"month": "2026-03"})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success(
        self,
        employee_client: AsyncClient,
        employee_user: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_user
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(employee_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["employee_id"] == profile.id
        assert data["full_name"] == "Петров Пётр"
        assert data["bonuses"] == ANY
        assert data["fines"] == ANY


class TestMyCalculate(TestView):
    URL = "/api/me/calculate"
    METHOD = "POST"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await client.post(
            self.URL,
            json={"month": "2026-03"},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success__no_overrides(
        self,
        employee_client: AsyncClient,
        employee_user: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_user
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        response = await employee_client.post(
            self.URL,
            json={"month": month},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["employee_id"] == profile.id
        assert data["full_name"] == "Петров Пётр"
        assert data["monthly_salary"] == ANY
        assert data["final_salary"] == ANY

    async def test_success__with_overrides(
        self,
        employee_client: AsyncClient,
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        response = await employee_client.post(
            self.URL,
            json={"month": month, "bonuses": 0, "fines": 0},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["monthly_salary"] == data["final_salary"]


class TestMyAdjustments(TestView):
    URL = "/api/me/adjustments"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success__all(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(employee_client)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        types = {a["type"] for a in data}
        assert "bonus" in types
        assert "fine" in types

    async def test_success__by_month(
        self,
        employee_client: AsyncClient,
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(employee_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 2  # noqa: PLR2004

    async def test_success__empty_month(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(
            employee_client,
            params={"month": "2020-01"},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []


class TestMyTimeEntries(TestView):
    URL = "/api/me/time-entries"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success__empty(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(employee_client)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    async def test_success__by_month(
        self,
        employee_client: AsyncClient,
    ) -> None:
        response = await self.request(
            employee_client,
            params={"month": "2020-01"},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []


class TestAuthMeEmployee(TestView):
    URL = "/api/auth/me"
    METHOD = "GET"

    async def test_success__includes_avatar_and_salary(
        self,
        employee_client: AsyncClient,
        session: AsyncSession,
        employee_user: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_user
        profile.avatar_key = "avatars/test.png"
        await session.flush()

        response = await self.request(employee_client)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["profile"] is not None
        assert data["profile"]["avatar_url"] is not None
        assert data["final_salary"] is not None
        assert data["shifts_count"] is not None
        assert data["total_hours"] is not None


class TestMyProfileNotFound(TestView):
    URL = "/api/me/profile"
    METHOD = "GET"

    async def test_error__employee_without_profile(
        self,
        session: AsyncSession,
        company: Company,
        transport: ASGITransport,
        app: FastAPI,
        fake_redis_client: FakeAsyncRedis,
    ) -> None:
        user = User(
            email=f"noprof_{uuid.uuid4().hex}@test.com",
            password_hash=hash_password("secret"),
            role="employee",
            company_id=company.id,
        )
        session.add(user)
        await session.flush()
        sid = await create_session(fake_redis_client, user.id)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            cookies={"session_id": str(sid)},
        ) as client:
            response = await client.get(self.URL)
        assert response.status_code == HTTPStatus.NOT_FOUND
