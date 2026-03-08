from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User
from tests.base import AuthTestView
from tests.controllers.employees.conftest import EMPLOYEE_PAYLOAD


class TestCreateEmployee(AuthTestView):
    URL = "/api/employees"
    METHOD = "POST"

    async def test_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        response = await self.request(auth_client, json=EMPLOYEE_PAYLOAD)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            "id": ANY,
            "email": "employee@test.com",
            "is_active": True,
            "profile": {
                "id": ANY,
                "user_id": ANY,
                "full_name": "Тестовый Сотрудник",
                "phone": "+79991234567",
                "position": "Разработчик",
                "rate_type": "hourly",
                "rate_amount": "500.00",
                "currency": "RUB",
                "created_at": ANY,
                "updated_at": None,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

        result = await session.execute(
            select(User).where(User.email == EMPLOYEE_PAYLOAD["email"]),
        )
        user = result.scalar_one()
        assert user.role == "employee"

    async def test_error__duplicate_email(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        payload = {**EMPLOYEE_PAYLOAD, "email": employee_user.email}
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json() == {
            "detail": "User with this email already exists",
        }

    async def test_success__with_schedule(
        self,
        auth_client: AsyncClient,
    ) -> None:
        payload = {
            **EMPLOYEE_PAYLOAD,
            "email": "scheduled@test.com",
            "schedule": [
                {
                    "date": "2027-01-15",
                    "start_time": "09:00:00",
                    "end_time": "18:00:00",
                },
            ],
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            "id": ANY,
            "email": "scheduled@test.com",
            "is_active": True,
            "profile": {
                "id": ANY,
                "user_id": ANY,
                "full_name": "Тестовый Сотрудник",
                "phone": "+79991234567",
                "position": "Разработчик",
                "rate_type": "hourly",
                "rate_amount": "500.00",
                "currency": "RUB",
                "created_at": ANY,
                "updated_at": None,
                "schedule": ANY,
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_success__minimal_fields(
        self,
        auth_client: AsyncClient,
    ) -> None:
        payload = {
            "email": "minimal@test.com",
            "password": "pass123",
            "full_name": "Минимальный Сотрудник",
            "position": "Стажёр",
            "rate_type": "shift",
            "rate_amount": "1000.00",
            "currency": "RUB",
        }
        response = await self.request(auth_client, json=payload)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            "id": ANY,
            "email": "minimal@test.com",
            "is_active": True,
            "profile": {
                "id": ANY,
                "user_id": ANY,
                "full_name": "Минимальный Сотрудник",
                "phone": None,
                "position": "Стажёр",
                "rate_type": "shift",
                "rate_amount": "1000.00",
                "currency": "RUB",
                "created_at": ANY,
                "updated_at": None,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }
