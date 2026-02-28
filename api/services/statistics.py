from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, EmployeeProfile, TimeEntry


async def calculate_work_quantity(
    db: AsyncSession,
    employee: EmployeeProfile,
    year: int,
    month: int,
) -> Decimal:
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.employee_id == employee.id,
            extract("year", TimeEntry.date) == year,
            extract("month", TimeEntry.date) == month,
            TimeEntry.check_out.is_not(None),
        ),
    )
    entries = result.scalars().all()

    if employee.rate_type == "hourly":
        total_hours = Decimal(0)
        for entry in entries:
            delta = entry.check_out - entry.check_in
            total_hours += Decimal(str(delta.total_seconds())) / Decimal(3600)
        return total_hours.quantize(Decimal("0.01"))

    if employee.rate_type == "shift":
        return Decimal(len(entries))

    if employee.rate_type == "daily":
        unique_days = {e.date for e in entries}
        return Decimal(len(unique_days))

    return Decimal(0)


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
    quantity = await calculate_work_quantity(db, employee, year, month)
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
    base_salary = employee.rate_amount * quantity
    total = base_salary + bonuses - fines

    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "position": employee.position,
        "rate_type": employee.rate_type,
        "rate_amount": employee.rate_amount,
        "currency": employee.currency,
        "quantity": quantity,
        "base_salary": base_salary,
        "bonuses": bonuses,
        "fines": fines,
        "total": total,
    }
