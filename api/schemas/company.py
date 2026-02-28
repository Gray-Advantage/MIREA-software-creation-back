from datetime import datetime

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
    logo: str | None = None
    legal_form: str
    legal_address: str
    contact_name: str
    business_area: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyUpdate(BaseModel):
    name: str | None = None
    logo: str | None = None
    legal_form: str | None = None
    legal_address: str | None = None
    contact_name: str | None = None
    business_area: str | None = None
    email: EmailStr | None = None
