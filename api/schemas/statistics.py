from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EmployeeSalary(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    position: str
    rate_type: str
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
