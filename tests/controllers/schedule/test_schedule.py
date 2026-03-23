from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, User
from tests.base import AuthTestView
from tests.controllers.schedule.conftest import SCHEDULE_ENTRY_COUNT


class TestMonthScheduleAll(AuthTestView):
    URL = "/api/schedule"
    METHOD = "GET"

    async def test_success__empty(
        self,
        auth_client: AsyncClient,
    ) -> None:
        today = datetime.now(UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["month"] == month
        assert len(data["days"]) > 0
        assert all(d["employees"] == [] for d in data["days"])

    async def test_success__with_employee(
        self,
        auth_client: AsyncClient,
        employee_with_schedule: User,
        session: AsyncSession,
    ) -> None:
        today = datetime.now(UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        days_with_staff = [d for d in data["days"] if d["employees"]]
        assert len(days_with_staff) == SCHEDULE_ENTRY_COUNT

        slot = days_with_staff[0]["employees"][0]
        assert slot == {
            "employee_id": ANY,
            "full_name": "Иванов Иван",
            "position": "Бариста",
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "rate_type": "hourly",
            "rate_amount": "500.00",
            "currency": "RUB",
        }

    async def test_error__missing_month(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(auth_client)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


class TestEmployeeSchedule(AuthTestView):
    URL = "/api/schedule/{employee_id}"
    METHOD = "GET"

    async def test_error__when_unauthorized(
        self,
        client: AsyncClient,
    ) -> None:
        response = await self.request(
            client,
            path={"employee_id": 0},
            params={"month": "2026-03"},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success(
        self,
        auth_client: AsyncClient,
        employee_with_schedule: User,
        session: AsyncSession,
    ) -> None:
        result = await session.execute(
            select(EmployeeProfile).where(
                EmployeeProfile.user_id == employee_with_schedule.id,
            ),
        )
        profile = result.scalar_one()

        today = datetime.now(UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(
            auth_client,
            path={"employee_id": profile.id},
            params={"month": month},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["employee_id"] == profile.id
        assert data["full_name"] == "Иванов Иван"
        assert data["position"] == "Бариста"
        assert data["month"] == month
        assert len(data["entries"]) == SCHEDULE_ENTRY_COUNT

        entry = data["entries"][0]
        assert entry == {
            "date": ANY,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "rate_type": "hourly",
            "rate_amount": "500.00",
            "currency": "RUB",
        }

    async def test_error__not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": 99999},
            params={"month": "2026-03"},
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
