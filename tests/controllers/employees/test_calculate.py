import datetime as dt
from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, User


async def test_calculate_employee_salary(
    auth_client: AsyncClient,
    employee_user: User,
    session: AsyncSession,
) -> None:
    result = await session.execute(
        select(EmployeeProfile).where(EmployeeProfile.user_id == employee_user.id),
    )
    profile = result.scalar_one()
    month = dt.datetime.now(dt.UTC).date().strftime("%Y-%m")

    response = await auth_client.post(
        f"/api/employees/{employee_user.id}/calculate",
        json={"month": month},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["employee_id"] == profile.id
    assert "final_salary" in data
