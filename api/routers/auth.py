from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_async_session
from api.deps import get_current_user
from api.models import ApiSession, Company, EmployeeProfile, User
from api.schemas.auth import LoginRequest, MeResponse, RegisterRequest
from api.schemas.company import CompanyRead
from api.schemas.employee import EmployeeProfileRead
from api.services.auth import hash_password, verify_password

router = APIRouter()

SESSION_TTL_DAYS = 30


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    existing = await db.execute(
        select(Company).where(Company.email == body.company.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this email already exists",
        )

    existing_user = await db.execute(
        select(User).where(User.email == body.email)
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

    session = ApiSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS),
    )
    db.add(session)
    await db.commit()

    response.set_cookie(
        key="session_id",
        value=str(session.id),
        path="/",
        httponly=True,
        max_age=SESSION_TTL_DAYS * 86400,
        samesite="lax",
    )

    return {"detail": "Registered successfully", "user_id": user.id}


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
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

    session = ApiSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS),
    )
    db.add(session)
    await db.commit()

    response.set_cookie(
        key="session_id",
        value=str(session.id),
        path="/",
        httponly=True,
        max_age=SESSION_TTL_DAYS * 86400,
        samesite="lax",
    )

    return {"detail": "Logged in", "role": user.role}


@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    await db.execute(
        select(ApiSession).where(ApiSession.user_id == user.id)
    )
    response.delete_cookie("session_id")
    return {"detail": "Logged out"}


@router.get("/me", response_model=MeResponse)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(User)
        .options(joinedload(User.company), joinedload(User.profile))
        .where(User.id == user.id)
    )
    full_user = result.unique().scalar_one()

    profile_data = None
    if full_user.profile:
        profile_data = EmployeeProfileRead.model_validate(full_user.profile)

    return MeResponse(
        id=full_user.id,
        email=full_user.email,
        role=full_user.role,
        company=CompanyRead.model_validate(full_user.company),
        profile=profile_data,
    )
