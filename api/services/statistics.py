import datetime as _dt
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, EmployeeProfile, Schedule

CENTS = Decimal("0.01")


def entry_hours(start_time: _dt.time, end_time: _dt.time) -> Decimal:
    start = _dt.datetime.combine(_dt.date.min, start_time)
    end = _dt.datetime.combine(_dt.date.min, end_time)
    diff = end - start
    if diff.total_seconds() < 0:
        diff += _dt.timedelta(days=1)
    return Decimal(str(diff.total_seconds() / 3600))


async def _compute_schedule_salary(
    db: AsyncSession,
    employee_id: int,
    year: int,
    month: int,
) -> tuple[Decimal, Decimal]:
    result = await db.execute(
        select(Schedule).where(
            Schedule.employee_id == employee_id,
            extract("year", Schedule.date) == year,
            extract("month", Schedule.date) == month,
        ),
    )
    entries = result.scalars().all()

    total = Decimal(0)
    quantity = Decimal(0)
    for entry in entries:
        if entry.rate_type == "hourly":
            hours = entry_hours(entry.start_time, entry.end_time)
            total += hours * entry.rate_amount
            quantity += hours
        else:
            total += entry.rate_amount
            quantity += 1

    return total.quantize(CENTS), quantity.quantize(CENTS)


async def calculate_adjustments_sum(
    db: AsyncSession,
    employee_id: int,
    year: int,
    month: int,
    adj_type: str,
) -> Decimal:
    result = await db.execute(
        select(func.coalesce(func.sum(Adjustment.amount), 0)).where(
            Adjustment.employee_id == employee_id,
            Adjustment.type == adj_type,
            extract("year", Adjustment.date) == year,
            extract("month", Adjustment.date) == month,
        ),
    )
    return result.scalar_one()


async def calculate_salary(
    db: AsyncSession,
    employee: EmployeeProfile,
    year: int,
    month: int,
) -> dict:
    base_salary, quantity = await _compute_schedule_salary(
        db,
        employee.id,
        year,
        month,
    )
    bonuses = await calculate_adjustments_sum(
        db,
        employee.id,
        year,
        month,
        "bonus",
    )
    fines = await calculate_adjustments_sum(
        db,
        employee.id,
        year,
        month,
        "fine",
    )
    bonuses = Decimal(bonuses).quantize(CENTS)
    fines = Decimal(fines).quantize(CENTS)
    total = (base_salary + bonuses - fines).quantize(CENTS)

    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "position": employee.position,
        "rate_type": employee.rate_type,
        "rate_amount": employee.rate_amount.quantize(CENTS),
        "currency": employee.currency,
        "quantity": quantity,
        "base_salary": base_salary,
        "bonuses": bonuses,
        "fines": fines,
        "total": total,
    }


def _compute_entries_salary(entries: list) -> tuple[Decimal, Decimal]:
    total = Decimal(0)
    quantity = Decimal(0)
    for entry in entries:
        if entry.rate_type == "hourly":
            hours = entry_hours(entry.start_time, entry.end_time)
            total += hours * entry.rate_amount
            quantity += hours
        else:
            total += entry.rate_amount
            quantity += 1
    return total.quantize(CENTS), quantity.quantize(CENTS)


async def calculate_with_overrides(  # noqa: PLR0913
    db: AsyncSession,
    employee: EmployeeProfile,
    year: int,
    month: int,
    *,
    schedule_overrides: list | None = None,
    exclude_dates: list | None = None,
    bonuses_override: Decimal | None = None,
    fines_override: Decimal | None = None,
) -> dict:
    result = await db.execute(
        select(Schedule).where(
            Schedule.employee_id == employee.id,
            extract("year", Schedule.date) == year,
            extract("month", Schedule.date) == month,
        ),
    )
    db_entries = list(result.scalars().all())

    today = _dt.datetime.now(_dt.UTC).date()
    if exclude_dates:
        excluded = set(exclude_dates)
        db_entries = [e for e in db_entries if e.date not in excluded or e.date < today]

    if schedule_overrides:
        override_dates = {e.date for e in schedule_overrides}
        merged = [e for e in db_entries if e.date not in override_dates]
        merged.extend(schedule_overrides)
    else:
        merged = db_entries

    base_salary, _quantity = _compute_entries_salary(merged)

    if bonuses_override is not None:
        bonuses = bonuses_override.quantize(CENTS)
    else:
        bonuses = Decimal(
            await calculate_adjustments_sum(db, employee.id, year, month, "bonus"),
        ).quantize(CENTS)

    if fines_override is not None:
        fines = fines_override.quantize(CENTS)
    else:
        fines = Decimal(
            await calculate_adjustments_sum(db, employee.id, year, month, "fine"),
        ).quantize(CENTS)

    final_salary = (base_salary + bonuses - fines).quantize(CENTS)

    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "currency": employee.currency,
        "monthly_salary": base_salary,
        "final_salary": final_salary,
    }
