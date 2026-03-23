import datetime as _dt
from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient

from api.models import EmployeeProfile, User
from tests.base import AuthTestView


class TestSalaryTable(AuthTestView):
    URL = "/api/statistics/salary"
    METHOD = "GET"

    async def test_success__empty(
        self,
        auth_client: AsyncClient,
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"month": month, "employees": []}

    async def test_success__with_employee(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["month"] == month
        assert len(data["employees"]) == 1

        # 3 * 8h * 600 = 14400, + 1000 - 300 = 15100
        assert data["employees"][0] == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "position": "Повар",
            "rate_type": "hourly",
            "rate_amount": ANY,
            "currency": "RUB",
            "quantity": ANY,
            "base_salary": 14400.0,
            "bonuses": 1000.0,
            "fines": 300.0,
            "total": 15100.0,
        }


class TestEmployeeSalary(AuthTestView):
    URL = "/api/statistics/salary/{employee_id}"
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
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(
            auth_client,
            path={"employee_id": profile.id},
            params={"month": month},
        )

        assert response.status_code == HTTPStatus.OK
        # 3 * 8h * 600 = 14400, + 1000 - 300 = 15100
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "position": "Повар",
            "rate_type": "hourly",
            "rate_amount": ANY,
            "currency": "RUB",
            "quantity": ANY,
            "base_salary": 14400.0,
            "bonuses": 1000.0,
            "fines": 300.0,
            "total": 15100.0,
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


class TestSummary(AuthTestView):
    URL = "/api/statistics/summary"
    METHOD = "GET"

    async def test_success__empty(
        self,
        auth_client: AsyncClient,
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "month": month,
            "total_employees": 0,
            "total_salary_fund": 0.0,
        }

    async def test_success__with_employee(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")
        response = await self.request(auth_client, params={"month": month})

        assert response.status_code == HTTPStatus.OK
        # 3 * 8h * 600 = 14400, + 1000 - 300 = 15100
        assert response.json() == {
            "month": month,
            "total_employees": 1,
            "total_salary_fund": 15100.0,
        }
