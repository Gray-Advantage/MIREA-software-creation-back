from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, User
from tests.base import AuthTestView


class TestDeleteEmployee(AuthTestView):
    URL = "/api/employees/{employee_id}"
    METHOD = "DELETE"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_success(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        employee_id = employee_user.id
        response = await self.request(
            auth_client,
            path={"employee_id": employee_id},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT

        result = await session.execute(
            select(User).where(User.id == employee_id),
        )
        assert result.scalar_one_or_none() is None

        result = await session.execute(
            select(EmployeeProfile).where(
                EmployeeProfile.user_id == employee_id,
            ),
        )
        assert result.scalar_one_or_none() is None

    async def test_success__employee_not_in_list_after_delete(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        list_response = await auth_client.get("/api/employees")
        assert list_response.status_code == HTTPStatus.OK
        assert list_response.json() == []

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
