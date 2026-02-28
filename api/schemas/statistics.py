from decimal import Decimal

from pydantic import BaseModel

from api.schemas.employee import RateType


class EmployeeSalary(BaseModel):
    employee_id: int
    full_name: str
    position: str
    rate_type: RateType
    rate_amount: Decimal
    currency: str
    quantity: Decimal
    base_salary: Decimal
    bonuses: Decimal
    fines: Decimal
    total: Decimal


class SalaryTableResponse(BaseModel):
    month: str
    employees: list[EmployeeSalary]


class SummaryResponse(BaseModel):
    month: str
    total_employees: int
    total_salary_fund: Decimal
