from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User
from tests.base import TestView
from tests.constants import DEFAULT_PASSWORD, DEFAULT_USER_EMAIL


class TestLogin(TestView):
    URL = "/api/auth/login"
    METHOD = "POST"

    async def test_success(
        self,
        client: AsyncClient,
        registered_user: User,
    ) -> None:
        response = await self.request(
            client,
            json={"email": DEFAULT_USER_EMAIL, "password": DEFAULT_PASSWORD},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"detail": "Logged in", "role": "admin"}
        assert "session_id" in response.cookies

    async def test_error__when_invalid_password(
        self,
        client: AsyncClient,
        registered_user: User,
    ) -> None:
        response = await self.request(
            client,
            json={"email": DEFAULT_USER_EMAIL, "password": "wrong_password"},
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {"detail": "Invalid email or password"}

    async def test_error__when_user_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        response = await self.request(
            client,
            json={
                "email": "nonexistent@test.com",
                "password": "any_password",
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {"detail": "Invalid email or password"}

    async def test_error__when_user_deactivated(
        self,
        client: AsyncClient,
        registered_user: User,
        session: AsyncSession,
    ) -> None:
        registered_user.is_active = False
        await session.flush()

        response = await self.request(
            client,
            json={"email": DEFAULT_USER_EMAIL, "password": DEFAULT_PASSWORD},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json() == {"detail": "Account is deactivated"}
