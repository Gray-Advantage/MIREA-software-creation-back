import datetime as _dt
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class AdjustmentType(str, Enum):
    bonus = "bonus"
    fine = "fine"


class AdjustmentCreate(BaseModel):
    type: AdjustmentType
    amount: Decimal
    comment: str
    date: _dt.date


class AdjustmentRead(BaseModel):
    id: int
    employee_id: int
    type: str
    amount: Decimal
    comment: str
    date: _dt.date
    created_at: datetime

    model_config = {"from_attributes": True}


class AdjustmentUpdate(BaseModel):
    type: AdjustmentType | None = None
    amount: Decimal | None = None
    comment: str | None = None
    date: _dt.date | None = None
