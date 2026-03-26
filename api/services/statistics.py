import datetime as _dt
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, EmployeeProfile, Schedule

CENTS = Decimal("0.01")


def _entry_hours(start_time: _dt.time, end_time: _dt.time) -> Decimal:
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
            hours = _entry_hours(entry.start_time, entry.end_time)
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


def calculate_from_input(
    schedule: list,
    bonuses: Decimal,
    fines: Decimal,
    currency: str,
) -> dict:
    total = Decimal(0)
    quantity = Decimal(0)
    for entry in schedule:
        if entry.rate_type == "hourly":
            hours = _entry_hours(entry.start_time, entry.end_time)
            total += hours * entry.rate_amount
            quantity += hours
        else:
            total += entry.rate_amount
            quantity += 1

    base_salary = total.quantize(CENTS)
    quantity = quantity.quantize(CENTS)
    bonuses = bonuses.quantize(CENTS)
    fines = fines.quantize(CENTS)
    total = (base_salary + bonuses - fines).quantize(CENTS)

    return {
        "currency": currency,
        "quantity": quantity,
        "base_salary": base_salary,
        "bonuses": bonuses,
        "fines": fines,
        "total": total,
    }
