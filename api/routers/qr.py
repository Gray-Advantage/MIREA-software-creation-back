from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin, require_employee
from api.models import EmployeeProfile, QRSession, TimeEntry, User
from api.schemas.responses import ADMIN, EMPLOYEE, R_400, R_404
from api.schemas.time_entry import (
    QRGenerateResponse,
    QRScanRequest,
    QRScanResponse,
)
from api.services.qr import generate_qr_image

router = APIRouter()

QR_TTL_MINUTES = 10


@router.post("/generate", responses={**ADMIN})
async def generate_qr(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> QRGenerateResponse:
    await db.execute(
        select(QRSession).where(
            QRSession.company_id == admin.company_id,
            QRSession.is_active.is_(True),
        ),
    )
    result = await db.execute(
        select(QRSession).where(
            QRSession.company_id == admin.company_id,
            QRSession.is_active.is_(True),
        ),
    )
    for old in result.scalars().all():
        old.is_active = False

    expires = datetime.now(UTC) + timedelta(minutes=QR_TTL_MINUTES)
    qr_session = QRSession(
        company_id=admin.company_id,
        expires_at=expires,
    )
    db.add(qr_session)
    await db.commit()
    await db.refresh(qr_session)

    qr_image = generate_qr_image(qr_session.token)

    return QRGenerateResponse(
        token=str(qr_session.token),
        qr_image_base64=qr_image,
        expires_at=expires,
    )


@router.post("/scan", responses={**EMPLOYEE, **R_400, **R_404})
async def scan_qr(
    body: QRScanRequest,
    employee_user: Annotated[User, Depends(require_employee)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> QRScanResponse:
    try:
        token = UUID(body.token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format",
        ) from None

    result = await db.execute(
        select(QRSession).where(
            QRSession.token == token,
            QRSession.is_active.is_(True),
            QRSession.expires_at > datetime.now(UTC),
            QRSession.company_id == employee_user.company_id,
        ),
    )
    qr_session = result.scalar_one_or_none()
    if qr_session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or wrong company QR code",
        )

    profile_result = await db.execute(
        select(EmployeeProfile).where(
            EmployeeProfile.user_id == employee_user.id,
        ),
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )

    open_entry_result = await db.execute(
        select(TimeEntry)
        .where(
            TimeEntry.employee_id == profile.id,
            TimeEntry.check_out.is_(None),
        )
        .order_by(TimeEntry.check_in.desc()),
    )
    open_entry = open_entry_result.scalar_one_or_none()

    now = datetime.now(UTC)

    if open_entry is None:
        entry = TimeEntry(
            employee_id=profile.id,
            date=now.date(),
            check_in=now,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return QRScanResponse(
            action="check_in",
            message="Check-in recorded",
            time_entry_id=entry.id,
        )
    open_entry.check_out = now
    await db.commit()
    return QRScanResponse(
        action="check_out",
        message="Check-out recorded",
        time_entry_id=open_entry.id,
    )


@router.get("/active", responses={**ADMIN})
async def get_active_qr(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict:
    result = await db.execute(
        select(QRSession).where(
            QRSession.company_id == admin.company_id,
            QRSession.is_active.is_(True),
            QRSession.expires_at > datetime.now(UTC),
        ),
    )
    qr_session = result.scalar_one_or_none()
    if qr_session is None:
        return {"active": False}

    qr_image = generate_qr_image(qr_session.token)
    return {
        "active": True,
        "token": str(qr_session.token),
        "qr_image_base64": qr_image,
        "expires_at": qr_session.expires_at,
    }
