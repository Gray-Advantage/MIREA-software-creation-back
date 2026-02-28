from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin
from api.models import Adjustment, EmployeeProfile, User
from api.schemas.adjustment import (
    AdjustmentCreate,
    AdjustmentRead,
    AdjustmentUpdate,
)

router = APIRouter()


async def _verify_employee_belongs_to_company(
    employee_id: int,
    admin: User,
    db: AsyncSession,
) -> EmployeeProfile:
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
    return profile


@router.get("/{employee_id}/adjustments")
async def list_adjustments(
    employee_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    adjustment_type: Annotated[
        str | None,
        Query(alias="type", pattern="^(bonus|fine)$"),
    ] = None,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
) -> list[AdjustmentRead]:
    await _verify_employee_belongs_to_company(employee_id, admin, db)

    query = select(Adjustment).where(Adjustment.employee_id == employee_id)
    if adjustment_type:
        query = query.where(Adjustment.type == adjustment_type)
    if month:
        year, m = map(int, month.split("-"))
        query = query.where(
            extract("year", Adjustment.date) == year,
            extract("month", Adjustment.date) == m,
        )
    query = query.order_by(Adjustment.date.desc())

    result = await db.execute(query)
    return [AdjustmentRead.model_validate(a) for a in result.scalars().all()]


@router.post(
    "/{employee_id}/adjustments",
    status_code=status.HTTP_201_CREATED,
)
async def create_adjustment(
    employee_id: int,
    body: AdjustmentCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> AdjustmentRead:
    await _verify_employee_belongs_to_company(employee_id, admin, db)

    adjustment = Adjustment(
        employee_id=employee_id,
        type=body.type.value,
        amount=body.amount,
        comment=body.comment,
        date=body.date,
    )
    db.add(adjustment)
    await db.commit()
    await db.refresh(adjustment)
    return AdjustmentRead.model_validate(adjustment)


@router.get(
    "/{employee_id}/adjustments/{adjustment_id}",
)
async def get_adjustment(
    employee_id: int,
    adjustment_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> AdjustmentRead:
    await _verify_employee_belongs_to_company(employee_id, admin, db)

    result = await db.execute(
        select(Adjustment).where(
            Adjustment.id == adjustment_id,
            Adjustment.employee_id == employee_id,
        ),
    )
    adjustment = result.scalar_one_or_none()
    if adjustment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adjustment not found",
        )
    return AdjustmentRead.model_validate(adjustment)


@router.patch(
    "/{employee_id}/adjustments/{adjustment_id}",
)
async def update_adjustment(
    employee_id: int,
    adjustment_id: int,
    body: AdjustmentUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> AdjustmentRead:
    await _verify_employee_belongs_to_company(employee_id, admin, db)

    result = await db.execute(
        select(Adjustment).where(
            Adjustment.id == adjustment_id,
            Adjustment.employee_id == employee_id,
        ),
    )
    adjustment = result.scalar_one_or_none()
    if adjustment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adjustment not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(
            adjustment,
            field,
            value.value if hasattr(value, "value") else value,
        )

    await db.commit()
    await db.refresh(adjustment)
    return AdjustmentRead.model_validate(adjustment)


@router.delete(
    "/{employee_id}/adjustments/{adjustment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_adjustment(
    employee_id: int,
    adjustment_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    await _verify_employee_belongs_to_company(employee_id, admin, db)

    result = await db.execute(
        select(Adjustment).where(
            Adjustment.id == adjustment_id,
            Adjustment.employee_id == employee_id,
        ),
    )
    adjustment = result.scalar_one_or_none()
    if adjustment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adjustment not found",
        )

    await db.delete(adjustment)
    await db.commit()
