import datetime as dt
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, User


@pytest.fixture
async def employee_profile(
    session: AsyncSession,
    employee_user: User,
) -> EmployeeProfile:
    result = await session.execute(
        select(EmployeeProfile).where(EmployeeProfile.user_id == employee_user.id),
    )
    return result.scalar_one()


async def test_adjustments_crud_and_filters(
    auth_client: AsyncClient,
    employee_profile: EmployeeProfile,
) -> None:
    eid = employee_profile.id
    d = dt.date(2026, 5, 10)

    create = await auth_client.post(
        f"/api/employees/{eid}/adjustments",
        json={
            "type": "bonus",
            "amount": "150.00",
            "comment": "тест",
            "date": d.isoformat(),
        },
    )
    assert create.status_code == HTTPStatus.CREATED
    adj_id = create.json()["id"]

    lst = await auth_client.get(
        f"/api/employees/{eid}/adjustments",
        params={"type": "bonus", "month": "2026-05"},
    )
    assert lst.status_code == HTTPStatus.OK
    assert len(lst.json()) >= 1

    one = await auth_client.get(
        f"/api/employees/{eid}/adjustments/{adj_id}",
    )
    assert one.status_code == HTTPStatus.OK
    assert one.json()["amount"] == "150.00"

    patched = await auth_client.patch(
        f"/api/employees/{eid}/adjustments/{adj_id}",
        json={"comment": "обновлено"},
    )
    assert patched.status_code == HTTPStatus.OK
    assert patched.json()["comment"] == "обновлено"

    deleted = await auth_client.delete(
        f"/api/employees/{eid}/adjustments/{adj_id}",
    )
    assert deleted.status_code == HTTPStatus.NO_CONTENT


async def test_adjustment_not_found(
    auth_client: AsyncClient,
    employee_profile: EmployeeProfile,
) -> None:
    eid = employee_profile.id
    r = await auth_client.get(f"/api/employees/{eid}/adjustments/999999")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_employee_not_found_for_adjustments(
    auth_client: AsyncClient,
) -> None:
    r = await auth_client.get("/api/employees/999999/adjustments")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_patch_and_delete_adjustment_not_found(
    auth_client: AsyncClient,
    employee_profile: EmployeeProfile,
) -> None:
    eid = employee_profile.id
    r = await auth_client.patch(
        f"/api/employees/{eid}/adjustments/999999",
        json={"comment": "x"},
    )
    assert r.status_code == HTTPStatus.NOT_FOUND

    d = await auth_client.delete(f"/api/employees/{eid}/adjustments/999999")
    assert d.status_code == HTTPStatus.NOT_FOUND
