from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient

from tests.base import AuthTestView
from tests.constants import (
    DEFAULT_COMPANY_EMAIL,
    DEFAULT_COMPANY_NAME,
    DEFAULT_USER_EMAIL,
)


class TestMe(AuthTestView):
    URL = "/api/auth/me"
    METHOD = "GET"

    async def test_success(self, auth_client: AsyncClient) -> None:
        response = await self.request(auth_client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "id": ANY,
            "email": DEFAULT_USER_EMAIL,
            "role": "admin",
            "company": {
                "id": ANY,
                "name": DEFAULT_COMPANY_NAME,
                "logo": None,
                "legal_form": "LLC",
                "legal_address": "123 Test Street",
                "contact_name": "Test Contact",
                "business_area": "IT",
                "email": DEFAULT_COMPANY_EMAIL,
                "inn": None,
                "bik": None,
                "created_at": ANY,
            },
            "profile": None,
        }
