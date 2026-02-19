from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin
from api.models import EmployeeProfile, TimeEntry, User
from api.schemas.time_entry import TimeEntryRead, TimeEntryUpdate

router = APIRouter()


@router.get("", response_model=list[TimeEntryRead])
async def list_time_entries(
    employee_id: Optional[int] = Query(default=None),
    month: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    query = (
        select(TimeEntry)
        .join(EmployeeProfile, TimeEntry.employee_id == EmployeeProfile.id)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(User.company_id == admin.company_id)
    )

    if employee_id is not None:
        query = query.where(EmployeeProfile.id == employee_id)
    if month:
        year, m = map(int, month.split("-"))
        query = query.where(
            extract("year", TimeEntry.date) == year,
            extract("month", TimeEntry.date) == m,
        )

    query = query.order_by(TimeEntry.date.desc(), TimeEntry.check_in.desc())
    result = await db.execute(query)
    return [TimeEntryRead.model_validate(e) for e in result.scalars().all()]


@router.get("/{entry_id}", response_model=TimeEntryRead)
async def get_time_entry(
    entry_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(TimeEntry)
        .join(EmployeeProfile, TimeEntry.employee_id == EmployeeProfile.id)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(TimeEntry.id == entry_id, User.company_id == admin.company_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
        )
    return TimeEntryRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=TimeEntryRead)
async def update_time_entry(
    entry_id: int,
    body: TimeEntryUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(TimeEntry)
        .join(EmployeeProfile, TimeEntry.employee_id == EmployeeProfile.id)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(TimeEntry.id == entry_id, User.company_id == admin.company_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    await db.commit()
    await db.refresh(entry)
    return TimeEntryRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    entry_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(TimeEntry)
        .join(EmployeeProfile, TimeEntry.employee_id == EmployeeProfile.id)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(TimeEntry.id == entry_id, User.company_id == admin.company_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
        )

    await db.delete(entry)
    await db.commit()
