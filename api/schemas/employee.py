from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class RateType(str, Enum):
    hourly = "hourly"
    shift = "shift"
    daily = "daily"


class Currency(str, Enum):
    RUB = "RUB"
    EUR = "EUR"
    USD = "USD"


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    position: str
    rate_type: RateType
    rate_amount: Decimal
    currency: Currency


class EmployeeProfileRead(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    position: str
    rate_type: str
    rate_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmployeeRead(BaseModel):
    id: int
    email: str
    is_active: bool
    profile: EmployeeProfileRead

    model_config = {"from_attributes": True}


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    position: Optional[str] = None
    rate_type: Optional[RateType] = None
    rate_amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    new_password: str
