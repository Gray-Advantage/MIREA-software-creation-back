from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_async_session
from api.deps import require_admin
from api.models import EmployeeProfile, User
from api.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    PasswordChange,
)
from api.services.auth import hash_password

router = APIRouter()


@router.get("")
async def list_employees(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    q: Annotated[
        str | None,
        Query(description="Поиск по email, ФИО, телефону, должности"),
    ] = None,
) -> list[EmployeeRead]:
    query = (
        select(User)
        .options(joinedload(User.profile))
        .where(User.company_id == admin.company_id, User.role == "employee")
    )
    if q and (term := q.strip()):
        term = f"%{term}%"
        query = query.join(EmployeeProfile, User.id == EmployeeProfile.user_id).where(
            or_(
                User.email.ilike(term),
                EmployeeProfile.full_name.ilike(term),
                EmployeeProfile.phone.ilike(term),
                EmployeeProfile.position.ilike(term),
            ),
        )
    result = await db.execute(query)
    users = result.unique().scalars().all()
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
    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)

    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=profile,
    )


async def _get_employee_user(
    employee_id: int,
    admin: User,
    db: AsyncSession,
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
    return user


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> EmployeeRead:
    user = await _get_employee_user(employee_id, admin, db)
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

    profile = user.profile
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(
                profile,
                field,
                value.value if hasattr(value, "value") else value,
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
