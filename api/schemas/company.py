from datetime import datetime

from pydantic import BaseModel, EmailStr


class CompanyCreate(BaseModel):
    name: str
    legal_form: str
    legal_address: str
    contact_name: str
    business_area: str
    email: EmailStr
    inn: str | None = None
    bik: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "ООО Ромашка",
                    "legal_form": "OOO",
                    "legal_address": "г. Москва, ул. Тестовая, д. 1",
                    "contact_name": "Иванов Иван",
                    "business_area": "IT",
                    "email": "info@romashka.ru",
                    "inn": "7707123456",
                    "bik": "044525225",
                },
            ],
        },
    }


class CompanyRead(BaseModel):
    id: int
    name: str
    logo: str | None = None
    legal_form: str
    legal_address: str
    contact_name: str
    business_area: str
    email: str
    inn: str | None = None
    bik: str | None = None
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
    inn: str | None = None
    bik: str | None = None
