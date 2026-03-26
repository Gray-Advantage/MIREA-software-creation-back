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


class TestCalculate(AuthTestView):
    URL = "/api/statistics/calculate"
    METHOD = "POST"

    async def test_error__employee_not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        payload = {
            "employee_id": 99999,
            "month": "2026-03",
        }
        response = await self.request(auth_client, json=payload)
        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_success__no_overrides_uses_db(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        payload = {
            "employee_id": profile.id,
            "month": month,
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.OK
        # 3 * 8h * 600 = 14400, + 1000 bonus - 300 fine = 15100
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "currency": "RUB",
            "quantity": 24.0,
            "base_salary": 14400.0,
            "bonuses": 1000.0,
            "fines": 300.0,
            "total": 15100.0,
        }

    async def test_success__override_bonuses_fines(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        payload = {
            "employee_id": profile.id,
            "month": month,
            "bonuses": 5000,
            "fines": 0,
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.OK
        # base stays 14400, overridden bonuses=5000, fines=0
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "currency": "RUB",
            "quantity": 24.0,
            "base_salary": 14400.0,
            "bonuses": 5000.0,
            "fines": 0.0,
            "total": 19400.0,
        }

    async def test_success__override_one_day(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        # DB has 3 days at day 5,6,7 with rate 600/h and 8h shifts
        # Override day 5 with rate 800/h (same hours)
        day5 = today.replace(day=5).isoformat()
        payload = {
            "employee_id": profile.id,
            "month": month,
            "schedule": [
                {
                    "date": day5,
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                    "rate_type": "hourly",
                    "rate_amount": 800,
                },
            ],
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.OK
        # day5: 8h * 800 = 6400, day6: 8h * 600 = 4800, day7: 8h * 600 = 4800
        # base = 16000, bonuses from DB = 1000, fines from DB = 300
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "currency": "RUB",
            "quantity": 24.0,
            "base_salary": 16000.0,
            "bonuses": 1000.0,
            "fines": 300.0,
            "total": 16700.0,
        }

    async def test_success__add_extra_day(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        # DB has days 5,6,7. Add day 10 — doesn't overlap, so it merges in.
        day10 = today.replace(day=10).isoformat()
        payload = {
            "employee_id": profile.id,
            "month": month,
            "schedule": [
                {
                    "date": day10,
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                    "rate_type": "hourly",
                    "rate_amount": 600,
                },
            ],
            "bonuses": 0,
            "fines": 0,
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.OK
        # 4 days * 8h * 600 = 19200
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "currency": "RUB",
            "quantity": 32.0,
            "base_salary": 19200.0,
            "bonuses": 0.0,
            "fines": 0.0,
            "total": 19200.0,
        }

    async def test_success__full_override(
        self,
        auth_client: AsyncClient,
        employee_with_schedule_and_adj: tuple[User, EmployeeProfile],
    ) -> None:
        _, profile = employee_with_schedule_and_adj
        today = _dt.datetime.now(_dt.UTC).date()
        month = today.strftime("%Y-%m")

        # Override all 3 existing days + bonuses + fines
        payload = {
            "employee_id": profile.id,
            "month": month,
            "schedule": [
                {
                    "date": today.replace(day=5).isoformat(),
                    "start_time": "08:00:00",
                    "end_time": "20:00:00",
                    "rate_type": "shift",
                    "rate_amount": 3000,
                },
                {
                    "date": today.replace(day=6).isoformat(),
                    "start_time": "08:00:00",
                    "end_time": "20:00:00",
                    "rate_type": "shift",
                    "rate_amount": 3000,
                },
                {
                    "date": today.replace(day=7).isoformat(),
                    "start_time": "08:00:00",
                    "end_time": "20:00:00",
                    "rate_type": "shift",
                    "rate_amount": 3000,
                },
            ],
            "bonuses": 500,
            "fines": 100,
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.OK
        # 3 shifts * 3000 = 9000
        assert response.json() == {
            "employee_id": profile.id,
            "full_name": "Петров Пётр",
            "currency": "RUB",
            "quantity": 3.0,
            "base_salary": 9000.0,
            "bonuses": 500.0,
            "fines": 100.0,
            "total": 9400.0,
        }
