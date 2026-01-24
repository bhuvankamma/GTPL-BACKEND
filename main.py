import os
import logging
import time
from collections import Counter
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from fastapi import (
    FastAPI, 
    HTTPException, 
    Body, 
    Depends, 
    Form, 
    WebSocket, 
    WebSocketDisconnect, 
    Query
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

# DB helpers
from db import get_cursor, get_db

# Unified Database Imports
try:
    from database import Base, engine, get_db
    from database_B import Base as Base_B, engine as engine_B
except ImportError:
    pass

try:
    from database_holiday import Base as HolidayBase, engine as HolidayEngine
except ImportError:
    pass

try:
    from database_policy import get_db_conn
except ImportError:
    pass

# Sumanth's DB & Utils
try:
    from database_su import get_db as get_db_su
    from crud.employee_tracking_websocket_manager import ConnectionManager
    from utils.Employee_tracking_geo import haversine
except ImportError:
    pass

# --- Routers ---
# Core Routers
from routes.candidate_evaluation import router as candidate_router
from routes.employee import router as employee_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router

# Sravya's Routers
from routes.routers_policy import router as policy_router
from routes.holidays_sravya import router as holidays_router
from routes.weekly_offs_sravya import router as weekly_offs_router
from routes.admin_rewards_sra import router as admin_rewards_router
from routes.manager_rewards_sra import router as manager_rewards_router
from routes.employee_rewards_sra import router as employee_rewards_router
from routes.bonus_rules_sra import router as bonus_rules_router
from routes.incentive_rules_sra import router as incentive_rules_router
from routes.manager_rules_sra import router as manager_rules_router

# Bhavani's Routers
from routes.course_creation import router as course_router
from routes.form12bb import router as form12bb_router
from routes.declaration_form12bb import router as declaration_router

# Likith's Routers
from routes.payroll_likith import router as payroll_router

# Sumanth's Routers
from routes.profile_employee_profile import router as profile_employee_router
from routes.profile_admin_profile import router as profile_admin_router
from routes.profile_employee_header import router as profile_employee_header_router

# Swapna's Router
from routes.ticketdashboard import router as ticket_router

from crud import employee_profile_edit

# ==================================================
# APP INIT
# ==================================================

app = FastAPI(title="HRMS Integrated Backend")
manager = ConnectionManager()

# Runtime Memory for Tracking
employees_live = {}
IDLE_TIME = 600        # 10 minutes
OFFLINE_TIME = 1800    # 30 minutes

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Core Tables Created")
except NameError:
    pass

try:
    HolidayBase.metadata.create_all(bind=HolidayEngine)
    print("✅ Holiday Tables Created")
except NameError:
    pass

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# ROUTER REGISTRATION
# ==================================================

# Core & Auth
app.include_router(auth_router, tags=["Auth"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(employee_router, tags=["Employee"])
app.include_router(candidate_router, prefix="/candidates", tags=["Candidate Evaluation"])

# Sumanth's Profile Routers
app.include_router(profile_employee_header_router, tags=["Profile Header"])
app.include_router(profile_employee_router, tags=["Employee Profile"])
app.include_router(profile_admin_router, tags=["Admin Profile"])

# Sravya's Modules
app.include_router(policy_router, tags=["Policies"])
app.include_router(holidays_router, prefix="/holidays", tags=["Holiday Calendar"])
app.include_router(weekly_offs_router, prefix="/weekly-offs", tags=["Holiday Calendar"])
app.include_router(admin_rewards_router, prefix="/rewards/admin", tags=["Rewards & Incentives"])
app.include_router(manager_rewards_router, prefix="/rewards/manager", tags=["Rewards & Incentives"])
app.include_router(employee_rewards_router, prefix="/rewards/employee", tags=["Rewards & Incentives"])
app.include_router(bonus_rules_router, prefix="/rules/bonus", tags=["Rewards & Incentives"])
app.include_router(incentive_rules_router, prefix="/rules/incentive", tags=["Rewards & Incentives"])
app.include_router(manager_rules_router, prefix="/rules/manager-rules", tags=["Rewards & Incentives"])

# Bhavani's Modules
app.include_router(course_router, prefix="/courses", tags=["Course Creation"])
app.include_router(form12bb_router, prefix="/form12bb", tags=["Form12BB"])
app.include_router(declaration_router, prefix="/declaration", tags=["Form12BB"])

# Likith's Modules
app.include_router(payroll_router, prefix="/payroll", tags=["Payroll"])

# Swapna's Module
app.include_router(ticket_router, prefix="/tickets", tags=["Ticket Dashboard"])

print("✅ ALL TEAM ROUTERS LOADED SUCCESSFULLY")

# ==================================================
# ROOT & DASHBOARD ENDPOINTS
# ==================================================

@app.get("/")
def root():
    return {"message": "HRMS Integrated API Running"}

class EmployeeCreate(BaseModel):
    emp_code: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    password: str
    status: Optional[str] = "Active"

@app.post("/employees")
def create_employee(emp: EmployeeCreate):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO employees (emp_code, first_name, last_name, email, department, password, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (emp.emp_code, emp.first_name, emp.last_name, emp.email, emp.department, emp.password, emp.status))
        conn.commit()
        return {"status": "employee_created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/employee/{emp_code}")
def get_profile(emp_code: str):
    profile = employee_profile_edit.get_employee_profile(emp_code)
    if not profile.get("employee"):
        raise HTTPException(status_code=404, detail="Employee not found")
    return profile

@app.put("/employee/{emp_code}/personal")
def update_personal(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_personal(emp_code, data)

@app.get("/dashboard/total-employees")
def total_employees():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM employees")
        return {"total_employees": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()

# ... (Additional profile/dashboard PUT/GET methods remain unchanged)

# ==================================================
# SUMANTH - LIVE TRACKING & WEBSOCKET
# ==================================================

@app.post("/api/login")
async def tracking_login(employeeId: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_su)):
    row = db.execute(text("SELECT emp_code, first_name FROM employees WHERE emp_code = :e AND password = :p"),
                    {"e": employeeId, "p": password}).fetchone()
    if not row: return {"ok": False}
    employees_live[employeeId] = {"name": row.first_name, "last_seen": time.time(), "status": "Active", "geofences": {}}
    await manager.broadcast({"type": "employee_online", "employeeId": employeeId})
    return {"ok": True}

@app.post("/api/location")
async def update_location(employeeId: str = Form(...), lat: float = Form(...), lng: float = Form(...), db: Session = Depends(get_db_su)):
    now = time.time()
    if employeeId not in employees_live: employees_live[employeeId] = {"name": employeeId, "geofences": {}}
    emp = employees_live[employeeId]
    emp.update({"last_seen": now, "lat": lat, "lng": lng})
    
    geofences = db.execute(text("SELECT * FROM geofences WHERE is_active = true")).fetchall()
    status, site = "Moving", None
    for g in geofences:
        dist = haversine(lat, lng, g.center_lat, g.center_lng)
        curr = "INSIDE" if dist <= g.radius_meters else "OUTSIDE"
        if curr == "INSIDE": status, site = "On-site", g.name
        if emp["geofences"].get(g.id) and emp["geofences"].get(g.id) != curr:
            event = "ENTER" if curr == "INSIDE" else "EXIT"
            db.execute(text("INSERT INTO geofence_events (emp_code, geofence_id, event_type, latitude, longitude) VALUES (:e, :g, :ev, :lat, :lng)"),
                       {"e": employeeId, "g": g.id, "ev": event, "lat": lat, "lng": lng})
            await manager.broadcast({"type": "geofence_event", "employeeId": employeeId, "site": g.name, "event": event})
        emp["geofences"][g.id] = curr
    emp.update({"status": status, "current_site": site})
    db.execute(text("INSERT INTO employee_locations (emp_code, latitude, longitude, geofence_status) VALUES (:e, :lat, :lng, :gs)"),
               {"e": employeeId, "lat": lat, "lng": lng, "gs": status})
    db.commit()
    return {"ok": True}

@app.websocket("/ws/admin")
async def admin_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)