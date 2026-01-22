from pydantic import BaseModel
from datetime import date
from typing import Optional, List
from typing import List

class WeeklyOffBulkUpdate(BaseModel):
    off_days: List[str]


class HolidayCreate(BaseModel):
    title: str
    date: date
    holiday_type: str
    description: Optional[str] = None
    recurring: str


class HolidayUpdate(HolidayCreate):
    pass


class WeeklyOffUpdate(BaseModel):
    day: str
    is_off: bool


# ✅ NEW: Bulk weekly-off update
class WeeklyOffBulkUpdate(BaseModel):
    off_days: List[str]
