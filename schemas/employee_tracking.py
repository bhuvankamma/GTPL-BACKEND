from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


# =====================================================
# AUTH / LOGIN
# =====================================================

class LoginResponse(BaseModel):
    ok: bool


# =====================================================
# LOCATION TRACKING
# =====================================================

class LocationUpdate(BaseModel):
    employeeId: str
    lat: float
    lng: float


class LocationPoint(BaseModel):
    lat: float
    lng: float
    timestamp: datetime


class LocationHistoryResponse(BaseModel):
    emp_code: str
    history: List[LocationPoint]


# =====================================================
# LIVE EMPLOYEE STATUS (ADMIN)
# =====================================================

class LiveEmployee(BaseModel):
    employeeId: str
    employeeName: Optional[str]
    current_site: Optional[str]
    status: str
    last_ping: str


# =====================================================
# GEOFENCE EVENTS
# =====================================================

class GeofenceEvent(BaseModel):
    site: str
    event: str
    time: datetime


# =====================================================
# FIELD WORK REPORTS
# =====================================================

class FieldWorkReportCreate(BaseModel):
    emp_code: str
    report_date: date
    client_name: str
    activities: str
    remarks: Optional[str] = None
    latitude: float
    longitude: float
    location_address: Optional[str] = None


class FieldWorkReportResponse(BaseModel):
    id: int
    emp_code: str
    report_date: date
    client_name: str
    activities: str
    remarks: Optional[str]
    latitude: float
    longitude: float
    location_address: Optional[str]
    geofence_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FieldWorkReportHistory(BaseModel):
    report_date: date
    client_name: str
    activities: str
    location: Optional[str]
    submitted_at: datetime


class AdminFieldWorkReport(BaseModel):
    employee: str
    date: date
    client: str
    activities: str
    location: Optional[str]
    geofence: Optional[str]
    time: datetime
