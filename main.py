from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from routes.course_creation import router
from database_B import Base, engine
from database import Base, engine
from sqlalchemy.orm import Session
from fastapi import FastAPI

# DB helpers
from db import get_db, get_cursor


# Routers
from routes.candidate_evaluation import router as candidate_router
from routes.employee import router as employee_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router

from crud import employee_profile_edit


# ==================================================
# APP INIT
# ==================================================

app = FastAPI(title="HRMS Backend")

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

app.include_router(
    auth_router,
    tags=["Auth"]
)

app.include_router(
    admin_router,
    tags=["Admin"]
)

app.include_router(
    employee_router,
    tags=["Employee"]
)

app.include_router(
    candidate_router,
    prefix="/candidates",
    tags=["Candidate Evaluation"]
)

# ==================================================
# EMPLOYEE CREATE (LEGACY)
# ==================================================

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
            emp.emp_code,
            emp.first_name,
            emp.last_name,
            emp.email,
            emp.department,
            emp.password,
            emp.status
        ))
        conn.commit()
        return {"status": "employee_created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ==================================================
# EMPLOYEE PROFILE
# ==================================================

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
    return employee_profile_edit.upsert_emergency_contacts(
        emp_code,
        data.get("contacts", [])
    )

# ==================================================
# LEAVE APPROVAL
# ==================================================

class LeaveApprove(BaseModel):
    leave_id: int


@app.post("/leave/approve")
def approve_leave(data: LeaveApprove):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            UPDATE leave_requests
            SET status='Approved'
            WHERE id=%s
        """, (data.leave_id,))
        conn.commit()
        return {"status": "leave_approved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ==================================================
# DASHBOARD SUMMARY
# ==================================================

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
        cur.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE date = CURRENT_DATE
              AND status='Present'
        """)
        return {"present_today": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/on-leave")
def on_leave():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM leave_requests
            WHERE status='Approved'
              AND CURRENT_DATE BETWEEN start_date AND end_date
        """)
        return {"on_leave": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/attendance-summary")
def attendance_summary():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT status, COUNT(*)
            FROM attendance
            WHERE date = CURRENT_DATE
            GROUP BY status
        """)
        return {row[0].lower(): row[1] for row in cur.fetchall()}
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/department-strength")
def department_strength():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT department, COUNT(*)
            FROM employees
            GROUP BY department
        """)
        return [{"department": r[0], "count": r[1]} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
        
# ==================================================
# COURSE CREATION
# ==================================================

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Course Creation API")
app.include_router(router)
