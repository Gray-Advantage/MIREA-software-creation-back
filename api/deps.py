from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_async_session
from api.models import ApiSession, User


async def get_db(session: AsyncSession = Depends(get_async_session)):
    yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    raw = request.cookies.get("session_id")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        session_id = UUID(raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    result = await db.execute(
        select(ApiSession)
        .options(joinedload(ApiSession.user).joinedload(User.company))
        .where(
            ApiSession.id == session_id,
            ApiSession.expires_at > datetime.now(timezone.utc),
        )
    )
    api_session = result.scalar_one_or_none()

    if api_session is None or not api_session.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return api_session.user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_employee(user: User = Depends(get_current_user)) -> User:
    if user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access required",
        )
    return user
