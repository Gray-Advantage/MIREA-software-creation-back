import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, Schedule, User
from api.routers.employees import (
    _apply_search_filters,
    _compute_final_salary,
    _compute_monthly_salary,
    _load_adjustments_for_month,
    _schedule_date_range,
)


def test_schedule_date_range_with_month() -> None:
    start, end = _schedule_date_range("2026-02")
    assert start == dt.date(2026, 2, 1)
    assert end.month == 2  # noqa: PLR2004


def test_schedule_date_range_without_month() -> None:
    start, end = _schedule_date_range(None)
    assert start < end


def test_compute_monthly_salary_hourly_overnight() -> None:
    d = dt.date(2026, 3, 1)
    sched = [
        Schedule(
            employee_id=1,
            date=d,
            start_time=dt.time(22, 0),
            end_time=dt.time(6, 0),
            rate_type="hourly",
            rate_amount=Decimal("100.00"),
            currency="RUB",
        ),
    ]
    total = _compute_monthly_salary(sched, "2026-03")
    assert total > Decimal(0)


def test_compute_monthly_salary_shift() -> None:
    d = dt.date(2026, 3, 1)
    sched = [
        Schedule(
            employee_id=1,
            date=d,
            start_time=dt.time(0, 0),
            end_time=dt.time(0, 0),
            rate_type="shift",
            rate_amount=Decimal("3000.00"),
            currency="RUB",
        ),
    ]
    assert _compute_monthly_salary(sched, "2026-03") == Decimal("3000.00")


def test_compute_final_salary() -> None:
    adj = [
        Adjustment(
            employee_id=1,
            type="bonus",
            amount=Decimal("100.00"),
            comment="",
            date=dt.date(2026, 1, 1),
        ),
        Adjustment(
            employee_id=1,
            type="fine",
            amount=Decimal("40.00"),
            comment="",
            date=dt.date(2026, 1, 1),
        ),
    ]
    out = _compute_final_salary(Decimal("1000.00"), adj)
    assert out == Decimal("1060.00")


def test_apply_search_filters_q() -> None:
    q = select(User).where(User.id > 0)
    filtered = _apply_search_filters(
        q,
        q="иван",
        full_name=None,
        contact=None,
        position=None,
    )
    assert filtered is not None


@pytest.mark.asyncio
async def test_load_adjustments_empty_profiles(session: AsyncSession) -> None:
    out = await _load_adjustments_for_month(session, [], "2026-03")
    assert out == {}
