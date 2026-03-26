import datetime as _dt
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

from api.schemas.employee import RateType

Money = Annotated[
    Decimal,
    PlainSerializer(
        lambda v: float(round(v, 2)),
        return_type=float,
    ),
]


class EmployeeSalary(BaseModel):
    employee_id: int
    full_name: str
    position: str
    rate_type: RateType
    rate_amount: Money
    currency: str
    quantity: Money
    base_salary: Money
    bonuses: Money
    fines: Money
    total: Money


class SalaryTableResponse(BaseModel):
    month: str
    employees: list[EmployeeSalary]


class SummaryResponse(BaseModel):
    month: str
    total_employees: int
    total_salary_fund: Money


class CalcScheduleEntry(BaseModel):
    date: _dt.date
    start_time: _dt.time
    end_time: _dt.time
    rate_type: RateType
    rate_amount: Decimal


class CalcRequest(BaseModel):
    employee_id: int
    month: str
    schedule: list[CalcScheduleEntry] | None = None
    bonuses: Decimal | None = None
    fines: Decimal | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_id": 1,
                    "month": "2026-04",
                    "schedule": [
                        {
                            "date": "2026-04-10",
                            "start_time": "09:00:00",
                            "end_time": "18:00:00",
                            "rate_type": "hourly",
                            "rate_amount": 500,
                        },
                    ],
                    "bonuses": 1000,
                    "fines": 200,
                },
            ],
        },
    }


class CalcResponse(BaseModel):
    employee_id: int
    full_name: str
    currency: str
    quantity: Money
    base_salary: Money
    bonuses: Money
    fines: Money
    total: Money
