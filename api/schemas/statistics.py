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
