from typing import Any

DEFAULT_USER_EMAIL = "admin@test.com"
DEFAULT_PASSWORD = "testpassword123"
DEFAULT_COMPANY_NAME = "Test Company"
DEFAULT_COMPANY_EMAIL = "company@test.com"

REGISTER_PAYLOAD: dict[str, Any] = {
    "email": DEFAULT_USER_EMAIL,
    "password": DEFAULT_PASSWORD,
    "company": {
        "name": DEFAULT_COMPANY_NAME,
        "legal_form": "LLC",
        "legal_address": "123 Test Street",
        "contact_name": "Test Contact",
        "business_area": "IT",
        "email": DEFAULT_COMPANY_EMAIL,
    },
}
