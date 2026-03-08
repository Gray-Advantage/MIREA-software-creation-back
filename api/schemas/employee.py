from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, EmailStr

from api.schemas.schedule import ScheduleEntry, ScheduleRead


class RateType(StrEnum):
    hourly = "hourly"
    shift = "shift"
    daily = "daily"


class Currency(StrEnum):
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
    schedule: list[ScheduleEntry] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "ivanov@example.com",
                    "password": "securePass123",
                    "full_name": "Иванов Иван Иванович",
                    "phone": "+79991234567",
                    "position": "Бариста",
                    "rate_type": "hourly",
                    "rate_amount": 350,
                    "currency": "RUB",
                    "schedule": [
                        {
                            "date": "2026-03-10",
                            "start_time": "09:00:00",
                            "end_time": "18:00:00",
                        },
                    ],
                },
            ],
        },
    }


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
    schedule: list[ScheduleRead] = []

    model_config = {"from_attributes": True}


class EmployeeRead(BaseModel):
    id: int
    email: str
    is_active: bool
    profile: EmployeeProfileRead
    monthly_salary: Decimal
    final_salary: Decimal

    model_config = {"from_attributes": True}


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    position: str | None = None
    rate_type: RateType | None = None
    rate_amount: Decimal | None = None
    currency: Currency | None = None
    is_active: bool | None = None
    schedule: list[ScheduleEntry] | None = None


class PasswordChange(BaseModel):
    new_password: str
