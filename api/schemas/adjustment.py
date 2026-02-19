from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AdjustmentType(str, Enum):
    bonus = "bonus"
    fine = "fine"


class AdjustmentCreate(BaseModel):
    type: AdjustmentType
    amount: Decimal
    comment: str
    date: date


class AdjustmentRead(BaseModel):
    id: int
    employee_id: int
    type: str
    amount: Decimal
    comment: str
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class AdjustmentUpdate(BaseModel):
    type: Optional[AdjustmentType] = None
    amount: Optional[Decimal] = None
    comment: Optional[str] = None
    date: Optional[date] = None
