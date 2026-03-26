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
    full_name: str
    phone: str | None = None
    position: str
    rate_type: RateType
    rate_amount: Decimal
    currency: Currency
    avatar_url: str | None = None
    schedule: list[ScheduleEntry] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "ivanov@example.com",
                    "full_name": "Иванов Иван Иванович",
                    "phone": "+79991234567",
                    "position": "Бариста",
                    "rate_type": "hourly",
                    "rate_amount": 350,
                    "currency": "RUB",
                    "avatar_url": "http://localhost:9000/stafftracker/avatars/abc123.jpeg",
                    "schedule": [
                        {
                            "date": "2026-04-10",
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
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    schedule: list[ScheduleRead] = []

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "user_id": 10,
                    "full_name": "Иванов Иван Иванович",
                    "phone": "+79991234567",
                    "position": "Бариста",
                    "rate_type": "hourly",
                    "rate_amount": "350.00",
                    "currency": "RUB",
                    "avatar_url": "http://localhost:9000/stafftracker/avatars/abc123.jpeg",
                    "created_at": "2026-03-01T12:00:00Z",
                    "updated_at": None,
                    "schedule": [
                        {
                            "date": "2026-04-10",
                            "start_time": "09:00:00",
                            "end_time": "18:00:00",
                            "rate_type": "hourly",
                            "rate_amount": "350.00",
                            "currency": "RUB",
                        },
                    ],
                },
            ],
        },
    }


class EmployeeRead(BaseModel):
    id: int
    email: str
    is_active: bool
    profile: EmployeeProfileRead
    monthly_salary: Decimal
    final_salary: Decimal

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 10,
                    "email": "ivanov@example.com",
                    "is_active": True,
                    "profile": {
                        "id": 1,
                        "user_id": 10,
                        "full_name": "Иванов Иван Иванович",
                        "phone": "+79991234567",
                        "position": "Бариста",
                        "rate_type": "hourly",
                        "rate_amount": "350.00",
                        "currency": "RUB",
                        "avatar_url": "http://localhost:9000/stafftracker/avatars/abc123.jpeg",
                        "created_at": "2026-03-01T12:00:00Z",
                        "updated_at": None,
                        "schedule": [
                            {
                                "date": "2026-04-10",
                                "start_time": "09:00:00",
                                "end_time": "18:00:00",
                                "rate_type": "hourly",
                                "rate_amount": "350.00",
                                "currency": "RUB",
                            },
                        ],
                    },
                    "monthly_salary": "3150.00",
                    "final_salary": "3650.00",
                },
            ],
        },
    }


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    position: str | None = None
    rate_type: RateType | None = None
    rate_amount: Decimal | None = None
    currency: Currency | None = None
    avatar_url: str | None = None
    is_active: bool | None = None
    schedule: list[ScheduleEntry] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "Иванов Иван Петрович",
                    "rate_amount": 400,
                },
                {
                    "schedule": [
                        {
                            "date": "2026-04-15",
                            "start_time": "10:00:00",
                            "end_time": "19:00:00",
                        },
                        {
                            "date": "2026-04-16",
                            "start_time": "10:00:00",
                            "end_time": "19:00:00",
                        },
                    ],
                },
                {
                    "is_active": False,
                },
            ],
        },
    }


class PasswordChange(BaseModel):
    new_password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "new_password": "newSecurePass456",
                },
            ],
        },
    }
