from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient

from api.models import User
from tests.base import AuthTestView


class TestGetEmployee(AuthTestView):
    URL = "/api/employees/{employee_id}"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
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
        }

    async def test_error__not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": 99999},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Employee not found"}

    async def test_error__other_company(
        self,
        auth_client: AsyncClient,
        other_company_employee: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": other_company_employee.id},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Employee not found"}
