from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, User
from tests.base import AuthTestView


class TestUpdateEmployee(AuthTestView):
    URL = "/api/employees/{employee_id}"
    METHOD = "PATCH"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success__update_name(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            json={"full_name": "Новое Имя"},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": {
                "id": ANY,
                "user_id": employee_user.id,
                "full_name": "Новое Имя",
                "phone": "+79991234567",
                "position": "Разработчик",
                "rate_type": "hourly",
                "rate_amount": "500.00",
                "currency": "RUB",
                "avatar_url": None,
                "created_at": ANY,
                "updated_at": ANY,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_success__update_rate(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            json={"rate_type": "daily", "rate_amount": "3000.00"},
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
                "rate_type": "daily",
                "rate_amount": "3000.00",
                "currency": "RUB",
                "avatar_url": None,
                "created_at": ANY,
                "updated_at": ANY,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_success__deactivate(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            json={"is_active": False},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": False,
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
                "updated_at": ANY,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_success__update_schedule(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            json={
                "schedule": [
                    {
                        "date": "2027-06-15",
                        "start_time": "10:00:00",
                        "end_time": "19:00:00",
                    },
                ],
            },
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
                "updated_at": ANY,
                "schedule": ANY,
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_success__clear_avatar_url(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        result = await session.execute(
            select(EmployeeProfile).where(EmployeeProfile.user_id == employee_user.id),
        )
        profile = result.scalar_one()
        profile.avatar_key = "avatars/clear_me.png"
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            json={"avatar_url": None},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["profile"]["avatar_url"] is None

    async def test_error__not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": 99999},
            json={"full_name": "Test"},
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
            json={"full_name": "Hack"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Employee not found"}
