from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Company, User
from tests.base import TestView
from tests.constants import REGISTER_PAYLOAD


class TestRegister(TestView):
    URL = "/api/auth/register"
    METHOD = "POST"

    async def test_success(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        response = await self.request(client, json=REGISTER_PAYLOAD)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            "detail": "Registered successfully",
            "user_id": ANY,
        }
        assert "session_id" in response.cookies

        result = await session.execute(
            select(User).where(User.email == REGISTER_PAYLOAD["email"]),
        )
        user = result.scalar_one()
        assert user.role == "admin"

        result = await session.execute(
            select(Company).where(
                Company.email == REGISTER_PAYLOAD["company"]["email"],
            ),
        )
        company = result.scalar_one()
        assert company.name == REGISTER_PAYLOAD["company"]["name"]

    async def test_error__when_company_email_already_exists(
        self,
        client: AsyncClient,
        registered_user: User,
    ) -> None:
        response = await self.request(client, json=REGISTER_PAYLOAD)

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()["detail"] == "Company with this email already exists"

    async def test_error__when_user_email_already_exists(
        self,
        client: AsyncClient,
        registered_user: User,
    ) -> None:
        payload = {
            **REGISTER_PAYLOAD,
            "company": {
                **REGISTER_PAYLOAD["company"],
                "email": "other@company.com",
            },
        }
        response = await self.request(client, json=payload)

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()["detail"] == "User with this email already exists"
