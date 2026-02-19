from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TimeEntryRead(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TimeEntryUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None


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
