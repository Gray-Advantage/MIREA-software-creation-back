import contextlib
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_async_session
from api.deps import get_current_user
from api.models import Company, EmployeeProfile, User
from api.redis_client import get_redis
from api.schemas.auth import LoginRequest, MeResponse, RegisterRequest
from api.schemas.company import CompanyRead
from api.schemas.employee import EmployeeProfileRead
from api.schemas.responses import R_401, R_403, R_409
from api.services import s3
from api.services.auth import hash_password, verify_password
from api.services.session_store import (
    SESSION_TTL_SECONDS,
    create_session,
    delete_session_for_user,
)
from api.services.statistics import calculate_salary, entry_hours

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, responses={**R_409})
async def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict:
    existing = await db.execute(
        select(Company).where(Company.email == body.company.email),
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this email already exists",
        )

    existing_user = await db.execute(
        select(User).where(User.email == body.email),
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    company = Company(
        name=body.company.name,
        legal_form=body.company.legal_form,
        legal_address=body.company.legal_address,
        contact_name=body.company.contact_name,
        business_area=body.company.business_area,
        email=body.company.email,
        inn=body.company.inn,
        bik=body.company.bik,
    )
    db.add(company)
    await db.flush()

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role="admin",
        company_id=company.id,
    )
    db.add(user)
    await db.flush()

    sid = await create_session(redis, user.id)
    await db.commit()

    response.set_cookie(
        key="session_id",
        value=str(sid),
        path="/",
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="lax",
    )

    return {"detail": "Registered successfully", "user_id": user.id}


@router.post("/login", responses={**R_401, **R_403})
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    sid = await create_session(redis, user.id)

    response.set_cookie(
        key="session_id",
        value=str(sid),
        path="/",
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="lax",
    )

    return {"detail": "Logged in", "role": user.role}


@router.post("/logout", responses={**R_401})
async def logout(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict:
    raw = request.cookies.get("session_id")
    if raw:
        with contextlib.suppress(ValueError):
            await delete_session_for_user(redis, UUID(raw), user.id)
    response.delete_cookie("session_id")
    return {"detail": "Logged out"}


@router.get("/me", responses={**R_401})
async def me(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> MeResponse:
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.company),
            joinedload(User.profile).selectinload(EmployeeProfile.schedule),
        )
        .where(User.id == user.id),
    )
    full_user = result.unique().scalar_one()

    profile_data = None
    final_salary = None
    shifts_count = None
    total_hours = None
    if full_user.profile:
        profile_data = EmployeeProfileRead.model_validate(full_user.profile)
        if full_user.profile.avatar_key:
            profile_data.avatar_url = s3.public_url(full_user.profile.avatar_key)

        now = datetime.now(UTC)
        salary_data = await calculate_salary(
            db,
            full_user.profile,
            now.year,
            now.month,
        )
        raw = Decimal(str(salary_data["total"]))
        final_salary = str(raw.quantize(Decimal("0.01")))

        schedule = full_user.profile.schedule or []
        current_month = [
            e for e in schedule if e.date.year == now.year and e.date.month == now.month
        ]
        shifts_count = len(current_month)
        total_hours = float(
            sum(entry_hours(e.start_time, e.end_time) for e in current_month)
        )

    return MeResponse(
        id=full_user.id,
        email=full_user.email,
        role=full_user.role,
        company=CompanyRead.model_validate(full_user.company),
        profile=profile_data,
        final_salary=final_salary,
        shifts_count=shifts_count,
        total_hours=total_hours,
    )
