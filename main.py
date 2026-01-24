import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

# DB helpers
from db import get_cursor, get_db

# Unified Database Imports (Handling both Core/Bhavani and Holiday/Likith setups)
try:
    from database import Base, engine, get_db
    # If Bhavani has a separate second database
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

# --- Routers ---
# Core Routers
from routes.candidate_evaluation import router as candidate_router
from routes.employee import router as employee_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router

# Sravya's Routers (Policies & Rewards)
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

from crud import employee_profile_edit

# ==================================================
# APP INIT
# ==================================================

app = FastAPI(title="HRMS Integrated Backend")

# Create tables for all SQLAlchemy models on startup
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

# Core
app.include_router(auth_router, tags=["Auth"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(employee_router, tags=["Employee"])
app.include_router(candidate_router, prefix="/candidates", tags=["Candidate Evaluation"])

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

print("✅ ALL TEAM ROUTERS LOADED SUCCESSFULLY")

# ==================================================
# ROOT & LEGACY ENDPOINTS
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
            INSERT INTO employees 
            (emp_code, first_name, last_name, email, department, password, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            emp.emp_code, emp.first_name, emp.last_name, 
            emp.email, emp.department, emp.password, emp.status
        ))
        conn.commit()
        return {"status": "employee_created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# --- Employee Profile Endpoints ---

@app.get("/employee/{emp_code}")
def get_profile(emp_code: str):
    profile = employee_profile_edit.get_employee_profile(emp_code)
    if not profile.get("employee"):
        raise HTTPException(status_code=404, detail="Employee not found")
    return profile

@app.put("/employee/{emp_code}/personal")
def update_personal(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_personal(emp_code, data)

@app.put("/employee/{emp_code}/official")
def update_official(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_official(emp_code, data)

@app.put("/employee/{emp_code}/family")
def update_family(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_family(emp_code, data)

@app.put("/employee/{emp_code}/vehicle")
def update_vehicle(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_vehicle(emp_code, data)

@app.put("/employee/{emp_code}/statutory")
def update_statutory(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.upsert_statutory(emp_code, data)

@app.put("/employee/{emp_code}/emergency-contacts")
def update_contacts(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.upsert_emergency_contacts(emp_code, data.get("contacts", []))

# --- Dashboard & Leave ---

class LeaveApprove(BaseModel):
    leave_id: int

@app.post("/leave/approve")
def approve_leave(data: LeaveApprove):
    conn, cur = get_cursor()
    try:
        cur.execute("UPDATE leave_requests SET status='Approved' WHERE id=%s", (data.leave_id,))
        conn.commit()
        return {"status": "leave_approved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

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
        cur.execute("""
            SELECT COUNT(*) FROM leave_requests 
            WHERE status='Approved' AND CURRENT_DATE BETWEEN start_date AND end_date
        """)
        return {"on_leave": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/attendance-summary")
def attendance_summary():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT status, COUNT(*) FROM attendance WHERE date = CURRENT_DATE GROUP BY status")
        return {row[0].lower(): row[1] for row in cur.fetchall()}
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/department-strength")
def department_strength():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
        return [{"department": r[0], "count": r[1]} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()