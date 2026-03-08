from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient

from api.models import User
from tests.base import AuthTestView


class TestListEmployees(AuthTestView):
    URL = "/api/employees"
    METHOD = "GET"

    async def test_success__empty(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    async def test_success__with_employee(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == [
            {
                "id": employee_user.id,
                "email": "employee@test.com",
                "is_active": True,
                "profile": {
                    "id": ANY,
                    "user_id": employee_user.id,
                    "full_name": "Тестовый Сотрудник",
                    "phone": "+79991234567",
                    "position": "Разработчик",
                    "rate_type": "hourly",
                    "rate_amount": "500.00",
                    "currency": "RUB",
                    "avatar_url": None,
                    "created_at": ANY,
                    "updated_at": None,
                    "schedule": [],
                },
                "monthly_salary": "0.00",
                "final_salary": "0.00",
            },
        ]

    async def test_success__search_by_name(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(auth_client, params={"q": "Тестовый"})

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) == 1

    async def test_success__search_by_email(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(auth_client, params={"q": "employee@"})

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) == 1

    async def test_success__search_no_match(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(auth_client, params={"q": "Несуществующий"})

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    async def test_success__does_not_show_other_company(
        self,
        auth_client: AsyncClient,
        other_company_employee: User,
    ) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []
