from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class CompanyCreate(BaseModel):
    name: str
    legal_form: str
    legal_address: str
    contact_name: str
    business_area: str
    email: EmailStr


class CompanyRead(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    legal_form: str
    legal_address: str
    contact_name: str
    business_area: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    legal_form: Optional[str] = None
    legal_address: Optional[str] = None
    contact_name: Optional[str] = None
    business_area: Optional[str] = None
    email: Optional[EmailStr] = None
