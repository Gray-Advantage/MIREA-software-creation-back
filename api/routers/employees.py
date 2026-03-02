import datetime as _dt
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import set_committed_value

from api.database import get_async_session
from api.deps import require_admin
from api.models import EmployeeProfile, Schedule, User
from api.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    PasswordChange,
)
from api.services.auth import hash_password


def _schedule_date_range(month: str | None) -> tuple[_dt.date, _dt.date]:
    if month:
        year, m = map(int, month.split("-"))
        start = _dt.date(year, m, 1)
        end = start + relativedelta(months=1) - _dt.timedelta(days=1)
    else:
        today = _dt.datetime.now(_dt.UTC).date()
        start = today.replace(day=1) - relativedelta(months=1)
        end = today.replace(day=1) + relativedelta(months=2) - _dt.timedelta(days=1)
    return start, end


router = APIRouter()


@router.get("")
async def list_employees(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    q: Annotated[
        str | None,
        Query(description="Поиск по email, ФИО, телефону, должности"),
    ] = None,
    month: Annotated[
        str | None,
        Query(
            pattern=r"^\d{4}-\d{2}$",
            description="Месяц расписания (YYYY-MM), по умолчанию ±1 от текущего",
        ),
    ] = None,
) -> list[EmployeeRead]:
    query = (
        select(User)
        .options(joinedload(User.profile))
        .where(User.company_id == admin.company_id, User.role == "employee")
    )
    if q and (term := q.strip()):
        term = f"%{term}%"
        query = query.join(
            EmployeeProfile,
            User.id == EmployeeProfile.user_id,
        ).where(
            or_(
                User.email.ilike(term),
                EmployeeProfile.full_name.ilike(term),
                EmployeeProfile.phone.ilike(term),
                EmployeeProfile.position.ilike(term),
            ),
        )
    result = await db.execute(query)
    users = result.unique().scalars().all()

    profiles = [u.profile for u in users if u.profile is not None]
    await _load_schedule_filtered(db, profiles, month)

    return [
        EmployeeRead(
            id=u.id,
            email=u.email,
            is_active=u.is_active,
            profile=u.profile,
        )
        for u in users
        if u.profile is not None
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    body: EmployeeCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> EmployeeRead:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role="employee",
        company_id=admin.company_id,
    )
    db.add(user)
    await db.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        full_name=body.full_name,
        phone=body.phone,
        position=body.position,
        rate_type=body.rate_type.value,
        rate_amount=body.rate_amount,
        currency=body.currency.value,
    )
    db.add(profile)
    await db.flush()

    if body.schedule:
        schedule_dicts = [e.model_dump() for e in body.schedule]
        set_committed_value(
            profile,
            "schedule",
            await _replace_schedule(db, profile.id, schedule_dicts),
        )

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)

    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=profile,
    )


async def _replace_schedule(
    db: AsyncSession,
    profile_id: int,
    entries: list[dict[str, object]],
) -> list[Schedule]:
    await db.execute(
        delete(Schedule).where(Schedule.employee_id == profile_id),
    )
    for entry in entries:
        db.add(
            Schedule(
                employee_id=profile_id,
                date=entry["date"],
                start_time=entry["start_time"],
                end_time=entry["end_time"],
            ),
        )
    await db.flush()
    rows = await db.execute(
        select(Schedule).where(Schedule.employee_id == profile_id),
    )
    return list(rows.scalars().all())


async def _load_schedule_filtered(
    db: AsyncSession,
    profiles: list[EmployeeProfile],
    month: str | None,
) -> None:
    if not profiles:
        return
    date_from, date_to = _schedule_date_range(month)
    profile_ids = [p.id for p in profiles]
    rows = await db.execute(
        select(Schedule).where(
            Schedule.employee_id.in_(profile_ids),
            Schedule.date >= date_from,
            Schedule.date <= date_to,
        ),
    )
    by_profile: dict[int, list[Schedule]] = {}
    for s in rows.scalars().all():
        by_profile.setdefault(s.employee_id, []).append(s)
    for p in profiles:
        set_committed_value(p, "schedule", by_profile.get(p.id, []))


async def _get_employee_user(
    employee_id: int,
    admin: User,
    db: AsyncSession,
    month: str | None = None,
) -> User:
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile))
        .where(
            User.id == employee_id,
            User.company_id == admin.company_id,
            User.role == "employee",
        ),
    )
    user = result.unique().scalar_one_or_none()
    if user is None or user.profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    await _load_schedule_filtered(db, [user.profile], month)
    return user


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    month: Annotated[
        str | None,
        Query(
            pattern=r"^\d{4}-\d{2}$",
            description="Месяц расписания (YYYY-MM), по умолчанию ±1 от текущего",
        ),
    ] = None,
) -> EmployeeRead:
    user = await _get_employee_user(employee_id, admin, db, month)
    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=user.profile,
    )


@router.patch("/{employee_id}")
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> EmployeeRead:
    user = await _get_employee_user(employee_id, admin, db)
    update_data = body.model_dump(exclude_unset=True)

    if "is_active" in update_data:
        user.is_active = update_data.pop("is_active")

    new_schedule = update_data.pop("schedule", None)

    profile = user.profile
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(
                profile,
                field,
                value.value if hasattr(value, "value") else value,
            )

    if new_schedule is not None:
        set_committed_value(
            profile,
            "schedule",
            await _replace_schedule(db, profile.id, new_schedule),
        )

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)

    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=profile,
    )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    user = await _get_employee_user(employee_id, admin, db)
    user.is_active = False
    await db.commit()


@router.patch("/{employee_id}/password")
async def change_employee_password(
    employee_id: int,
    body: PasswordChange,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    user = await _get_employee_user(employee_id, admin, db)
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"detail": "Password changed"}
