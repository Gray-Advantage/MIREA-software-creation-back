import datetime as _dt
from datetime import datetime

from pydantic import BaseModel


class TimeEntryRead(BaseModel):
    id: int
    employee_id: int
    date: _dt.date
    check_in: datetime
    check_out: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TimeEntryUpdate(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None


class QRScanRequest(BaseModel):
    token: str


class QRScanResponse(BaseModel):
    action: str
    message: str
    time_entry_id: int


class QRGenerateResponse(BaseModel):
    token: str
    qr_image_base64: str
    expires_at: datetime
