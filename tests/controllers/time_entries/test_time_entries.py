import datetime as dt
from datetime import UTC
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EmployeeProfile, TimeEntry, User


@pytest.fixture
async def employee_profile(
    session: AsyncSession,
    employee_user: User,
) -> EmployeeProfile:
    result = await session.execute(
        select(EmployeeProfile).where(EmployeeProfile.user_id == employee_user.id),
    )
    return result.scalar_one()


async def test_time_entries_list_get_patch_delete(
    auth_client: AsyncClient,
    employee_profile: EmployeeProfile,
    session: AsyncSession,
) -> None:
    check_in = dt.datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    entry = TimeEntry(
        employee_id=employee_profile.id,
        date=check_in.date(),
        check_in=check_in,
        check_out=None,
    )
    session.add(entry)
    await session.flush()

    lst = await auth_client.get("/api/time-entries")
    assert lst.status_code == HTTPStatus.OK
    assert len(lst.json()) >= 1

    by_emp = await auth_client.get(
        "/api/time-entries",
        params={"employee_id": employee_profile.id},
    )
    assert by_emp.status_code == HTTPStatus.OK

    month_q = await auth_client.get(
        "/api/time-entries",
        params={"month": "2026-06"},
    )
    assert month_q.status_code == HTTPStatus.OK

    one = await auth_client.get(f"/api/time-entries/{entry.id}")
    assert one.status_code == HTTPStatus.OK

    patched = await auth_client.patch(
        f"/api/time-entries/{entry.id}",
        json={"check_out": "2026-06-01T18:00:00Z"},
    )
    assert patched.status_code == HTTPStatus.OK

    deleted = await auth_client.delete(f"/api/time-entries/{entry.id}")
    assert deleted.status_code == HTTPStatus.NO_CONTENT


async def test_time_entry_not_found(auth_client: AsyncClient) -> None:
    r = await auth_client.get("/api/time-entries/999999")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_patch_and_delete_time_entry_not_found(
    auth_client: AsyncClient,
) -> None:
    r = await auth_client.patch(
        "/api/time-entries/999999",
        json={"check_out": "2026-06-01T18:00:00Z"},
    )
    assert r.status_code == HTTPStatus.NOT_FOUND

    d = await auth_client.delete("/api/time-entries/999999")
    assert d.status_code == HTTPStatus.NOT_FOUND
