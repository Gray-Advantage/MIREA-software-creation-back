import datetime as _dt

from pydantic import BaseModel


class ScheduleEntry(BaseModel):
    date: _dt.date
    start_time: _dt.time
    end_time: _dt.time


class ScheduleRead(ScheduleEntry):
    model_config = {"from_attributes": True}


class EmployeeSlot(BaseModel):
    employee_id: int
    full_name: str
    position: str
    start_time: _dt.time
    end_time: _dt.time


class DaySchedule(BaseModel):
    date: _dt.date
    employees: list[EmployeeSlot]


class MonthScheduleResponse(BaseModel):
    month: str
    days: list[DaySchedule]
