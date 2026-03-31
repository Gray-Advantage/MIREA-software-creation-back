import datetime as _dt
from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient

from api.models import EmployeeProfile, User
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
