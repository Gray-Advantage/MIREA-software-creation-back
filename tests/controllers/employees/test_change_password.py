from http import HTTPStatus

from httpx import AsyncClient

from api.models import User
from tests.base import AuthTestView


class TestChangeEmployeePassword(AuthTestView):
    URL = "/api/employees/{employee_id}/password"
    METHOD = "PATCH"

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
            json={"new_password": "newpass123"},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"detail": "Password changed"}

    async def test_error__not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": 99999},
            json={"new_password": "newpass123"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Employee not found"}
