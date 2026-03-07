from http import HTTPStatus

from httpx import AsyncClient

from tests.base import AuthTestView


class TestLogout(AuthTestView):
    URL = "/api/auth/logout"
    METHOD = "POST"

    async def test_success(self, auth_client: AsyncClient) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"detail": "Logged out"}
