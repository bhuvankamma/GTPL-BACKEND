from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class TimezoneEnum(str, Enum):
    IST = "IST"
    EST = "EST"
    GMT = "GMT"

class DateFormatEnum(str, Enum):
    DDMMYYYY = "DD/MM/YYYY"
    MMDDYYYY = "MM/DD/YYYY"
    YYYYMMDD = "YYYY-MM-DD"

class SettingsCreate(BaseModel):
    system_name: str = Field(..., example="HRMS Command Center")
    timezone: TimezoneEnum
    date_format: DateFormatEnum

class SettingsOut(BaseModel):
    id: int
    system_name: str
    timezone: str
    date_format: str
