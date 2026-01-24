from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from db import Base

class DeviceAssignmentRule(Base):
    __tablename__ = "device_assignment_rules"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("biometric_devices.id"))
    applies_to = Column(String(100))
    location_context = Column(String(100))
    access_schedule = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
