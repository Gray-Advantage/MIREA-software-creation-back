import datetime as _dt
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, EmployeeProfile, Schedule


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
            start = _dt.datetime.combine(_dt.date.min, entry.start_time)
            end = _dt.datetime.combine(_dt.date.min, entry.end_time)
            diff = end - start
            if diff.total_seconds() < 0:
                diff += _dt.timedelta(days=1)
            hours = Decimal(str(diff.total_seconds() / 3600))
            total += hours * entry.rate_amount
            quantity += hours
        else:
            total += entry.rate_amount
            quantity += 1

    cents = Decimal("0.01")
    return total.quantize(cents), quantity.quantize(cents)


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
    cents = Decimal("0.01")
    bonuses = Decimal(bonuses).quantize(cents)
    fines = Decimal(fines).quantize(cents)
    total = (base_salary + bonuses - fines).quantize(cents)

    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "position": employee.position,
        "rate_type": employee.rate_type,
        "rate_amount": employee.rate_amount.quantize(cents),
        "currency": employee.currency,
        "quantity": quantity,
        "base_salary": base_salary,
        "bonuses": bonuses,
        "fines": fines,
        "total": total,
    }
