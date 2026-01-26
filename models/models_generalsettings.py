# app/models.py
import enum
from sqlalchemy import Column, Integer, String, Date, Enum
from database_B import Base

class TimezoneEnum(str, enum.Enum):
    IST = "IST"
    EST = "EST"
    GMT = "GMT"

class DateFormatEnum(str, enum.Enum):
    DDMMYYYY = "DD/MM/YYYY"
    MMDDYYYY = "MM/DD/YYYY"
    YYYYMMDD = "YYYY-MM-DD"


class Settings(Base):
    __tablename__ = "general_settings"

    id = Column(Integer, primary_key=True)
    system_name = Column(String(255), nullable=False)
    timezone = Column(String(10), nullable=False)
    date_format = Column(String(20), nullable=False)
