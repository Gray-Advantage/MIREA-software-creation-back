import datetime as _dt
from collections import defaultdict
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin
from api.models import EmployeeProfile, Schedule, User
from api.schemas.responses import ADMIN, ADMIN_NOT_FOUND
from api.schemas.schedule import (
    DaySchedule,
    EmployeeScheduleResponse,
    EmployeeSlot,
    MonthScheduleResponse,
    ScheduleRead,
)

router = APIRouter()


def _month_range(month: str) -> tuple[_dt.date, _dt.date]:
    year, m = map(int, month.split("-"))
    date_from = _dt.date(year, m, 1)
    date_to = date_from + relativedelta(months=1) - _dt.timedelta(days=1)
    return date_from, date_to


@router.get("", responses={**ADMIN})
async def month_schedule(
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> MonthScheduleResponse:
    date_from, date_to = _month_range(month)

    rows = await db.execute(
        select(Schedule, EmployeeProfile)
        .join(EmployeeProfile, Schedule.employee_id == EmployeeProfile.id)
        .join(User, EmployeeProfile.user_id == User.id)
        .where(
            User.company_id == admin.company_id,
            User.is_active.is_(True),
            Schedule.date >= date_from,
            Schedule.date <= date_to,
        )
        .order_by(Schedule.date, Schedule.start_time),
    )

    by_day: dict[_dt.date, list[EmployeeSlot]] = defaultdict(list)
    for sched, profile in rows.all():
        by_day[sched.date].append(
            EmployeeSlot(
                employee_id=profile.id,
                full_name=profile.full_name,
                position=profile.position,
                start_time=sched.start_time,
                end_time=sched.end_time,
                rate_type=sched.rate_type,
                rate_amount=sched.rate_amount,
                currency=sched.currency,
            ),
        )

    current = date_from
    days: list[DaySchedule] = []
    while current <= date_to:
        days.append(
            DaySchedule(
                date=current,
                employees=by_day.get(current, []),
            ),
        )
        current += _dt.timedelta(days=1)

    return MonthScheduleResponse(month=month, days=days)


@router.get("/{employee_id}", responses={**ADMIN_NOT_FOUND})
async def employee_schedule(
    employee_id: int,
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> EmployeeScheduleResponse:
    date_from, date_to = _month_range(month)

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

    rows = await db.execute(
        select(Schedule)
        .where(
            Schedule.employee_id == employee_id,
            Schedule.date >= date_from,
            Schedule.date <= date_to,
        )
        .order_by(Schedule.date, Schedule.start_time),
    )

    return EmployeeScheduleResponse(
        employee_id=profile.id,
        full_name=profile.full_name,
        position=profile.position,
        month=month,
        entries=[ScheduleRead.model_validate(s) for s in rows.scalars().all()],
    )
