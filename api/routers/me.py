from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_employee
from api.models import Adjustment, EmployeeProfile, TimeEntry, User
from api.schemas.adjustment import AdjustmentRead
from api.schemas.employee import EmployeeProfileRead
from api.schemas.statistics import EmployeeSalary
from api.schemas.time_entry import TimeEntryRead
from api.services.statistics import calculate_salary

router = APIRouter()


async def _get_profile(user: User, db: AsyncSession) -> EmployeeProfile:
    result = await db.execute(
        select(EmployeeProfile).where(EmployeeProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return profile


@router.get("/profile", response_model=EmployeeProfileRead)
async def get_my_profile(
    user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_async_session),
):
    profile = await _get_profile(user, db)
    return EmployeeProfileRead.model_validate(profile)


@router.get("/salary", response_model=EmployeeSalary)
async def get_my_salary(
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_async_session),
):
    profile = await _get_profile(user, db)
    year, m = map(int, month.split("-"))
    data = await calculate_salary(db, profile, year, m)
    return EmployeeSalary(**data)


@router.get("/adjustments", response_model=list[AdjustmentRead])
async def get_my_adjustments(
    month: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_async_session),
):
    profile = await _get_profile(user, db)

    query = select(Adjustment).where(Adjustment.employee_id == profile.id)
    if month:
        year, m = map(int, month.split("-"))
        query = query.where(
            extract("year", Adjustment.date) == year,
            extract("month", Adjustment.date) == m,
        )
    query = query.order_by(Adjustment.date.desc())
    result = await db.execute(query)
    return [AdjustmentRead.model_validate(a) for a in result.scalars().all()]


@router.get("/time-entries", response_model=list[TimeEntryRead])
async def get_my_time_entries(
    month: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_async_session),
):
    profile = await _get_profile(user, db)

    query = select(TimeEntry).where(TimeEntry.employee_id == profile.id)
    if month:
        year, m = map(int, month.split("-"))
        query = query.where(
            extract("year", TimeEntry.date) == year,
            extract("month", TimeEntry.date) == m,
        )
    query = query.order_by(TimeEntry.date.desc(), TimeEntry.check_in.desc())
    result = await db.execute(query)
    return [TimeEntryRead.model_validate(e) for e in result.scalars().all()]
