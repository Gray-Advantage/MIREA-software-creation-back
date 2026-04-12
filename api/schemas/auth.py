from pydantic import BaseModel, EmailStr

from api.schemas.company import CompanyCreate, CompanyRead
from api.schemas.employee import EmployeeProfileRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company: CompanyCreate


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeResponse(BaseModel):
    id: int
    email: str
    role: str
    company: CompanyRead
    profile: EmployeeProfileRead | None = None
    final_salary: str | None = None
    shifts_count: int | None = None
    total_hours: float | None = None
