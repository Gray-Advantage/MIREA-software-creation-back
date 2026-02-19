from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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


@router.get("", response_model=list[EmployeeRead])
async def list_employees(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile))
        .where(User.company_id == admin.company_id, User.role == "employee")
    )
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


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: EmployeeCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
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
        first_name=body.first_name,
        last_name=body.last_name,
        patronymic=body.patronymic,
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
    employee_id: int, admin: User, db: AsyncSession
) -> User:
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile))
        .where(
            User.id == employee_id,
            User.company_id == admin.company_id,
            User.role == "employee",
        )
    )
    user = result.unique().scalar_one_or_none()
    if user is None or user.profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    return user


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    user = await _get_employee_user(employee_id, admin, db)
    return EmployeeRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        profile=user.profile,
    )


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    user = await _get_employee_user(employee_id, admin, db)
    update_data = body.model_dump(exclude_unset=True)

    if "is_active" in update_data:
        user.is_active = update_data.pop("is_active")

    profile = user.profile
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value.value if hasattr(value, "value") else value)

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
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    user = await _get_employee_user(employee_id, admin, db)
    user.is_active = False
    await db.commit()


@router.patch("/{employee_id}/password")
async def change_employee_password(
    employee_id: int,
    body: PasswordChange,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    user = await _get_employee_user(employee_id, admin, db)
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"detail": "Password changed"}
