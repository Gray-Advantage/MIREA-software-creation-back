from datetime import datetime
from decimal import Decimal
from enum import Enum

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
    full_name: str
    phone: str | None = None
    position: str
    rate_type: RateType
    rate_amount: Decimal
    currency: Currency


class EmployeeProfileRead(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str | None = None
    position: str
    rate_type: RateType
    rate_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class EmployeeRead(BaseModel):
    id: int
    email: str
    is_active: bool
    profile: EmployeeProfileRead

    model_config = {"from_attributes": True}


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    position: str | None = None
    rate_type: RateType | None = None
    rate_amount: Decimal | None = None
    currency: Currency | None = None
    is_active: bool | None = None


class PasswordChange(BaseModel):
    new_password: str
