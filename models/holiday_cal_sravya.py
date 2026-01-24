from sqlalchemy import Column, Integer, String, Date, Boolean, Text, TIMESTAMP
from database_holiday import Base
from sqlalchemy.sql import func


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    holiday_type = Column(String(50), nullable=False)
    description = Column(Text)
    recurring = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class WeeklyOff(Base):
    __tablename__ = "weekly_offs"

    id = Column(Integer, primary_key=True)
    day = Column(String(10), unique=True, nullable=False)
    is_off = Column(Boolean, default=False)
