from sqlalchemy import Column, String, Float, Integer,Date,Text, DateTime, Boolean, ForeignKey
from datetime import datetime
from app.database import Base
from sqlalchemy.sql import func



class Employee(Base):
    __tablename__ = "employees"

    emp_code = Column(String, primary_key=True)
    first_name = Column(String)
    password = Column(String)


class EmployeeLocation(Base):
    __tablename__ = "employee_locations"

    id = Column(Integer, primary_key=True)
    emp_code = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    geofence_id = Column(Integer)
    geofence_status = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    center_lat = Column(Float)
    center_lng = Column(Float)
    radius_meters = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GeofenceEvent(Base):
    __tablename__ = "geofence_events"

    id = Column(Integer, primary_key=True)
    emp_code = Column(String)
    geofence_id = Column(Integer)
    event_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    ts = Column(DateTime, default=datetime.utcnow)


class FieldWorkReport(Base):
    __tablename__ = "field_work_reports"

    id = Column(Integer, primary_key=True)

    emp_code = Column(String(50), index=True)

    report_date = Column(Date, nullable=False)

    client_name = Column(String(150))

    activities = Column(Text)

    remarks = Column(Text)

    latitude = Column(Float)
    longitude = Column(Float)

    location_address = Column(String(255))

    geofence_id = Column(Integer, ForeignKey("geofences.id"))
    geofence_status = Column(String(20))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )