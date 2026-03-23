import datetime as _dt
import secrets
import uuid
from decimal import Decimal
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import delete, extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import set_committed_value

from api.database import get_async_session
from api.deps import require_admin
from api.models import (
    Adjustment,
    ApiSession,
    EmployeeProfile,
    Schedule,
    TimeEntry,
    User,
)
from api.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    PasswordChange,
)
from api.schemas.responses import ADMIN, ADMIN_NOT_FOUND, R_409
from api.services import s3
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


def _compute_monthly_salary(
    schedule: list[Schedule],
    month: str | None,
) -> Decimal:
    if month:
        year, m = map(int, month.split("-"))
    else:
        today = _dt.datetime.now(_dt.UTC).date()
        year, m = today.year, today.month

    entries = [s for s in schedule if s.date.year == year and s.date.month == m]

    total = Decimal(0)
    for entry in entries:
        if entry.rate_type == "hourly":
            start = _dt.datetime.combine(_dt.date.min, entry.start_time)
            end = _dt.datetime.combine(_dt.date.min, entry.end_time)
            diff = end - start
            if diff.total_seconds() < 0:
                diff += _dt.timedelta(days=1)
            hours = Decimal(str(diff.total_seconds() / 3600))
            total += hours * entry.rate_amount
        else:
            total += entry.rate_amount

    return total.quantize(Decimal("0.01"))


def _compute_final_salary(
    monthly_salary: Decimal,
    adjustments: list[Adjustment],
) -> Decimal:
    bonuses = sum(
        (a.amount for a in adjustments if a.type == "bonus"),
        Decimal(0),
    )
    fines = sum(
        (a.amount for a in adjustments if a.type == "fine"),
        Decimal(0),
    )
    return (monthly_salary + bonuses - fines).quantize(Decimal("0.01"))


async def _load_adjustments_for_month(
    db: AsyncSession,
    profile_ids: list[int],
    month: str | None,
) -> dict[int, list[Adjustment]]:
    if not profile_ids:
        return {}
    if month:
        year, m = map(int, month.split("-"))
    else:
        today = _dt.datetime.now(_dt.UTC).date()
        year, m = today.year, today.month

    rows = await db.execute(
        select(Adjustment).where(
            Adjustment.employee_id.in_(profile_ids),
            extract("year", Adjustment.date) == year,
            extract("month", Adjustment.date) == m,
        ),
    )
    by_profile: dict[int, list[Adjustment]] = {}
    for a in rows.scalars().all():
        by_profile.setdefault(a.employee_id, []).append(a)
    return by_profile


async def _delete_avatar(profile: EmployeeProfile) -> None:
    if profile.avatar_key:
        await s3.delete(profile.avatar_key)
        profile.avatar_key = None


def _build_employee_response(
    user: User,
    profile: EmployeeProfile,
    month: str | None = None,
    adjustments: list[Adjustment] | None = None,
) -> EmployeeRead:
    salary = _compute_monthly_salary(profile.schedule, month)
    final = _compute_final_salary(salary, adjustments or [])

    from api.schemas.employee import EmployeeProfileRead

    profile_read = EmployeeProfileRead.model_validate(profile)
    if profile.avatar_key:
        profile_read.avatar_url = f"/api/employees/{user.id}/avatar"

    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=profile_read,
        monthly_salary=salary,
        final_salary=final,
    )


def _apply_search_filters(  # noqa: C901
    query: select,
    *,
    q: str | None,
    full_name: str | None,
    contact: str | None,
    position: str | None,
) -> select:
    has_specific = any(f and f.strip() for f in [full_name, contact, position])
    has_q = bool(q and q.strip())

    if has_specific or has_q:
        query = query.join(
            EmployeeProfile,
            User.id == EmployeeProfile.user_id,
        )

    if has_q:
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                User.email.ilike(term),
                EmployeeProfile.full_name.ilike(term),
                EmployeeProfile.phone.ilike(term),
                EmployeeProfile.position.ilike(term),
            ),
        )

    if full_name and (term := full_name.strip()):
        query = query.where(EmployeeProfile.full_name.ilike(f"%{term}%"))
    if contact and (term := contact.strip()):
        pat = f"%{term}%"
        query = query.where(
            or_(User.email.ilike(pat), EmployeeProfile.phone.ilike(pat)),
        )
    if position and (term := position.strip()):
        query = query.where(EmployeeProfile.position.ilike(f"%{term}%"))
    return query


router = APIRouter()


@router.get("", responses={**ADMIN})
async def list_employees(  # noqa: PLR0913
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    q: Annotated[
        str | None,
        Query(description="Общий поиск по email, ФИО, телефону, должности"),
    ] = None,
    full_name: Annotated[
        str | None,
        Query(description="Фильтр по ФИО"),
    ] = None,
    contact: Annotated[
        str | None,
        Query(description="Фильтр по email / телефону"),
    ] = None,
    position: Annotated[
        str | None,
        Query(description="Фильтр по должности"),
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

    query = _apply_search_filters(
        query,
        q=q,
        full_name=full_name,
        contact=contact,
        position=position,
    )

    result = await db.execute(query)
    users = result.unique().scalars().all()

    profiles = [u.profile for u in users if u.profile is not None]
    await _load_schedule_filtered(db, profiles, month)
    adj_map = await _load_adjustments_for_month(
        db,
        [p.id for p in profiles],
        month,
    )

    return [
        _build_employee_response(
            u,
            u.profile,
            month,
            adj_map.get(u.profile.id, []),
        )
        for u in users
        if u.profile is not None
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={**ADMIN, **R_409},
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
        password_hash=hash_password(secrets.token_urlsafe(16)),
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
            await _replace_schedule(
                db,
                profile.id,
                schedule_dicts,
                body.rate_type.value,
                body.rate_amount,
                body.currency.value,
            ),
        )

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    await _load_schedule_filtered(db, [profile], None)

    return _build_employee_response(user, profile, adjustments=[])


async def _replace_schedule(  # noqa: PLR0913
    db: AsyncSession,
    profile_id: int,
    entries: list[dict[str, object]],
    rate_type: str,
    rate_amount: Decimal,
    currency: str,
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
                rate_type=rate_type,
                rate_amount=rate_amount,
                currency=currency,
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


@router.get("/{employee_id}", responses={**ADMIN_NOT_FOUND})
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
    adj_map = await _load_adjustments_for_month(
        db,
        [user.profile.id],
        month,
    )
    return _build_employee_response(
        user,
        user.profile,
        month,
        adj_map.get(user.profile.id, []),
    )


@router.patch("/{employee_id}", responses={**ADMIN_NOT_FOUND})
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
            await _replace_schedule(
                db,
                profile.id,
                new_schedule,
                profile.rate_type,
                profile.rate_amount,
                profile.currency,
            ),
        )

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    await _load_schedule_filtered(db, [profile], None)
    adj_map = await _load_adjustments_for_month(db, [profile.id], None)

    return _build_employee_response(
        user,
        profile,
        adjustments=adj_map.get(profile.id, []),
    )


@router.put("/{employee_id}/avatar", responses={**ADMIN_NOT_FOUND})
async def upload_avatar(
    employee_id: int,
    file: UploadFile,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    user = await _get_employee_user(employee_id, admin, db)
    profile = user.profile

    data = await file.read()
    content_type = file.content_type or "image/jpeg"
    ext = content_type.split("/")[-1]
    key = f"avatars/{profile.id}_{uuid.uuid4().hex}.{ext}"

    if profile.avatar_key:
        await s3.delete(profile.avatar_key)

    await s3.upload(key, data, content_type)
    profile.avatar_key = key
    await db.commit()

    return {"avatar_url": f"/api/employees/{user.id}/avatar"}


@router.get("/{employee_id}/avatar", responses={**ADMIN_NOT_FOUND})
async def get_avatar(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Response:
    user = await _get_employee_user(employee_id, admin, db)
    if not user.profile.avatar_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )
    data, content_type = await s3.download(user.profile.avatar_key)
    return Response(content=data, media_type=content_type)


@router.delete(
    "/{employee_id}/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**ADMIN_NOT_FOUND},
)
async def delete_avatar(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    user = await _get_employee_user(employee_id, admin, db)
    await _delete_avatar(user.profile)
    await db.commit()


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**ADMIN_NOT_FOUND},
)
async def delete_employee(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    user = await _get_employee_user(employee_id, admin, db)
    profile = user.profile

    if profile.avatar_key:
        await s3.delete(profile.avatar_key)

    await db.execute(
        delete(Schedule).where(Schedule.employee_id == profile.id),
    )
    await db.execute(
        delete(Adjustment).where(Adjustment.employee_id == profile.id),
    )
    await db.execute(
        delete(TimeEntry).where(TimeEntry.employee_id == profile.id),
    )
    await db.execute(
        delete(EmployeeProfile).where(EmployeeProfile.id == profile.id),
    )
    await db.execute(
        delete(ApiSession).where(ApiSession.user_id == user.id),
    )
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()


@router.patch("/{employee_id}/password", responses={**ADMIN_NOT_FOUND})
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
