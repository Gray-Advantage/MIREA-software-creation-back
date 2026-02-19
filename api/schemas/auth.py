from __future__ import annotations

from typing import Optional

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
    profile: Optional[EmployeeProfileRead] = None
