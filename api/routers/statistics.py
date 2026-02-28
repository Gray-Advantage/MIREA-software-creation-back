from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin
from api.models import EmployeeProfile, User
from api.schemas.statistics import (
    EmployeeSalary,
    SalaryTableResponse,
    SummaryResponse,
)
from api.services.statistics import calculate_salary

router = APIRouter()


@router.get("/salary")
async def salary_table(
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SalaryTableResponse:
    year, m = map(int, month.split("-"))

    result = await db.execute(
        select(EmployeeProfile)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(User.company_id == admin.company_id, User.is_active.is_(True)),
    )
    profiles = result.scalars().all()

    employees = []
    for profile in profiles:
        data = await calculate_salary(db, profile, year, m)
        employees.append(EmployeeSalary(**data))

    return SalaryTableResponse(month=month, employees=employees)


@router.get("/salary/{employee_id}")
async def employee_salary(
    employee_id: int,
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> EmployeeSalary:
    year, m = map(int, month.split("-"))

    result = await db.execute(
        select(EmployeeProfile)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(
            EmployeeProfile.id == employee_id,
            User.company_id == admin.company_id,
        ),
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    data = await calculate_salary(db, profile, year, m)
    return EmployeeSalary(**data)


@router.get("/summary")
async def summary(
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SummaryResponse:
    year, m = map(int, month.split("-"))

    result = await db.execute(
        select(EmployeeProfile)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(User.company_id == admin.company_id, User.is_active.is_(True)),
    )
    profiles = result.scalars().all()

    total_fund = Decimal(0)
    for profile in profiles:
        data = await calculate_salary(db, profile, year, m)
        total_fund += data["total"]

    return SummaryResponse(
        month=month,
        total_employees=len(profiles),
        total_salary_fund=total_fund,
    )
