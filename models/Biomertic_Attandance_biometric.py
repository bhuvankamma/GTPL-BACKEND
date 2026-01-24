from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from db import Base

class BiometricDevice(Base):
    __tablename__ = "biometric_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String(150), nullable=False)
    device_type = Column(String(50), nullable=False)
    api_endpoint = Column(String, nullable=False)
    physical_location = Column(String(150))
    status = Column(String(30), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
