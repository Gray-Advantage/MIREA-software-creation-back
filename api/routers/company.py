from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_async_session
from api.deps import require_admin
from api.models import User
from api.schemas.company import CompanyRead, CompanyUpdate

router = APIRouter()


@router.get("")
async def get_company(
    user: Annotated[User, Depends(require_admin)],
) -> CompanyRead:
    return CompanyRead.model_validate(user.company)


@router.patch("")
async def update_company(
    body: CompanyUpdate,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> CompanyRead:
    company = user.company
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return CompanyRead.model_validate(company)
