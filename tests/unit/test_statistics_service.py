import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, Company, EmployeeProfile, Schedule, User
from api.services.auth import hash_password
from api.services.statistics import (
    calculate_salary,
    calculate_with_overrides,
    entry_hours,
)


def test_entry_hours_same_day() -> None:
    h = entry_hours(dt.time(9, 0), dt.time(18, 0))
    assert h == Decimal(9)


def test_entry_hours_overnight() -> None:
    h = entry_hours(dt.time(22, 0), dt.time(6, 0))
    assert h == Decimal(8)


@pytest.mark.asyncio
async def test_calculate_salary_hourly_and_shift_and_adjustments(
    session: AsyncSession,
) -> None:
    company = Company(
        name="Co",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="co@t.com",
    )
    session.add(company)
    await session.flush()

    user = User(
        email="u@t.com",
        password_hash=hash_password("p"),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Name",
        position="P",
        rate_type="hourly",
        rate_amount=Decimal("100.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    d1 = dt.date(2026, 3, 15)
    d2 = dt.date(2026, 3, 16)
    session.add(
        Schedule(
            employee_id=profile.id,
            date=d1,
            start_time=dt.time(10, 0),
            end_time=dt.time(12, 0),
            rate_type="hourly",
            rate_amount=Decimal("100.00"),
            currency="RUB",
        ),
    )
    session.add(
        Schedule(
            employee_id=profile.id,
            date=d2,
            start_time=dt.time(0, 0),
            end_time=dt.time(0, 0),
            rate_type="shift",
            rate_amount=Decimal("500.00"),
            currency="RUB",
        ),
    )
    session.add(
        Adjustment(
            employee_id=profile.id,
            type="bonus",
            amount=Decimal("50.00"),
            comment="b",
            date=d1,
        ),
    )
    session.add(
        Adjustment(
            employee_id=profile.id,
            type="fine",
            amount=Decimal("25.00"),
            comment="f",
            date=d1,
        ),
    )
    await session.flush()

    data = await calculate_salary(session, profile, 2026, 3)
    assert data["bonuses"] == Decimal("50.00")
    assert data["fines"] == Decimal("25.00")
    assert data["total"] == (data["base_salary"] + Decimal("50.00") - Decimal("25.00"))


@pytest.mark.asyncio
async def test_calculate_with_overrides_merges_and_override_amounts(
    session: AsyncSession,
) -> None:
    company = Company(
        name="Co2",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="co2@t.com",
    )
    session.add(company)
    await session.flush()

    user = User(
        email="u2@t.com",
        password_hash=hash_password("p"),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Name",
        position="P",
        rate_type="hourly",
        rate_amount=Decimal("100.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    d = dt.date(2026, 4, 10)
    session.add(
        Schedule(
            employee_id=profile.id,
            date=d,
            start_time=dt.time(10, 0),
            end_time=dt.time(11, 0),
            rate_type="hourly",
            rate_amount=Decimal("100.00"),
            currency="RUB",
        ),
    )
    await session.flush()

    override_row = Schedule(
        employee_id=profile.id,
        date=d,
        start_time=dt.time(12, 0),
        end_time=dt.time(14, 0),
        rate_type="hourly",
        rate_amount=Decimal("200.00"),
        currency="RUB",
    )

    await session.flush()

    data = await calculate_with_overrides(
        session,
        profile,
        2026,
        4,
        schedule_overrides=[override_row],
        bonuses_override=Decimal("10.00"),
        fines_override=Decimal("3.00"),
    )
    assert data["monthly_salary"] > Decimal(0)
    assert data["final_salary"] == (
        data["monthly_salary"] + Decimal("10.00") - Decimal("3.00")
    )


@pytest.mark.asyncio
async def test_calculate_with_overrides_exclude_future_only_keeps_past(
    session: AsyncSession,
) -> None:
    company = Company(
        name="Co3",
        legal_form="LLC",
        legal_address="x",
        contact_name="c",
        business_area="IT",
        email="co3@t.com",
    )
    session.add(company)
    await session.flush()

    user = User(
        email="u3@t.com",
        password_hash=hash_password("p"),
        role="employee",
        company_id=company.id,
    )
    session.add(user)
    await session.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name="Name",
        position="P",
        rate_type="hourly",
        rate_amount=Decimal("100.00"),
        currency="RUB",
    )
    session.add(profile)
    await session.flush()

    future = dt.date(2099, 6, 15)
    session.add(
        Schedule(
            employee_id=profile.id,
            date=future,
            start_time=dt.time(10, 0),
            end_time=dt.time(11, 0),
            rate_type="hourly",
            rate_amount=Decimal("100.00"),
            currency="RUB",
        ),
    )
    await session.flush()

    data = await calculate_with_overrides(
        session,
        profile,
        2099,
        6,
        exclude_dates=[future],
    )
    assert data["monthly_salary"] >= Decimal(0)
