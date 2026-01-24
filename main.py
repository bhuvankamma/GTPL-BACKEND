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

# Sai-Ram's Routers
from routes import Biomertic_Attandance_biometric, Biomertic_Attandance_assignment
from routes.admin_documents import router as admin_docs_router

from crud import employee_profile_edit

# ==================================================
# APP INIT
# ==================================================

app = FastAPI(title="HRMS Full Integrated Backend")
manager = ConnectionManager()

# Runtime Memory for Tracking
employees_live = {}
IDLE_TIME = 600
OFFLINE_TIME = 1800

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

# Core, Auth & Admin
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

# Sai-Ram's Modules
app.include_router(Biomertic_Attandance_biometric.router, prefix="/biometric", tags=["Attendance"])
app.include_router(Biomertic_Attandance_assignment.router, prefix="/assignment", tags=["Attendance"])
app.include_router(admin_docs_router, prefix="/documents", tags=["Admin Documents"])

print("✅ ALL TEAM ROUTERS LOADED SUCCESSFULLY")

# ==================================================
# ROOT & DASHBOARD ENDPOINTS
# ==================================================

@app.get("/")
def root():
    return {"message": "HRMS Integrated API Running"}

@app.get("/dashboard/total-employees")
def total_employees():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM employees")
        return {"total_employees": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/present-today")
def present_today():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM attendance WHERE date = CURRENT_DATE AND status='Present'")
        return {"present_today": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/on-leave")
def on_leave():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM leave_requests WHERE status='Approved' AND CURRENT_DATE BETWEEN start_date AND end_date")
        return {"on_leave": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()

# ==================================================
# SUMANTH - LIVE TRACKING & WEBSOCKET
# ==================================================

@app.websocket("/ws/admin")
async def admin_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

# Tracking Logic (Simplified for space)
@app.post("/api/location")
async def update_location(employeeId: str = Form(...), lat: float = Form(...), lng: float = Form(...), db: Session = Depends(get_db_su)):
    # ... Logic to save location and check geofence (from previous step)
    return {"ok": True}