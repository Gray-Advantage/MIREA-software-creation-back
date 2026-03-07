from http import HTTPStatus

from httpx import AsyncClient

from tests.base import AuthTestView
from tests.constants import DEFAULT_COMPANY_NAME, DEFAULT_USER_EMAIL


class TestMe(AuthTestView):
    URL = "/api/auth/me"
    METHOD = "GET"

    async def test_success(self, auth_client: AsyncClient) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data["email"] == DEFAULT_USER_EMAIL
        assert data["role"] == "admin"
        assert data["company"]["name"] == DEFAULT_COMPANY_NAME
        assert data["profile"] is None
