from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, date
import jwt
import json
import os
from passlib.hash import pbkdf2_sha256
from main import get_connection

router = APIRouter(prefix="", tags=["HR Dashboard"])

# ---------------------- CONFIG ----------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8
ALLOWED_ROLES = {"admin", "hr"}
# --------------------------------------------------


# ---------------------- MODELS ----------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    expires_in_hours: int


class EmployeeCreate(BaseModel):
    emp_code: str
    full_name: str
    email: str
    department: Optional[str] = None
    department_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = "Active"
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    aadhaar_ssn: Optional[str] = None
    designation: Optional[str] = None
    manager: Optional[str] = None
    date_of_joining: Optional[date] = None
    basic_salary: Optional[float] = None
    allowances: Optional[dict] = None


class LeaveApprove(BaseModel):
    leave_id: int


class AnnouncementCreate(BaseModel):
    title: str
    message: str


class RewardCreate(BaseModel):
    emp_code: str
    reward_title: str
    reward_description: Optional[str] = None


# ---------------------- JWT HELPERS ----------------------
def create_token(payload: dict):
    exp = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload["exp"] = exp
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(authorization: str = Header(...)):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split()[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    role = (payload.get("role") or "").lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return payload


# ---------------------- AUTH ----------------------
@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, first_name, last_name, email, password_hash, role
        FROM users WHERE email=%s
    """, (data.email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, first_name, last_name, email, password_hash, role = row

    if not pbkdf2_sha256.verify(data.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "user_id": user_id,
        "email": email,
        "role": role,
        "first_name": first_name,
        "last_name": last_name
    })

    return {"token": token, "expires_in_hours": JWT_EXPIRE_HOURS}


# ---------------------- DASHBOARD ----------------------
@router.get("/dashboard/total-employees")
def total_employees(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees")
    total = cur.fetchone()[0]
    conn.close()
    return {"total_employees": total}


@router.get("/dashboard/present-today")
def present_today(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=%s AND status='present'",
        (today,)
    )
    present = cur.fetchone()[0]
    conn.close()
    return {"present_today": present}


@router.get("/dashboard/on-leave")
def on_leave(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM leave_requests
        WHERE %s BETWEEN start_date AND end_date
        AND status='Approved'
    """, (today,))
    count = cur.fetchone()[0]
    conn.close()
    return {"on_leave": count}


@router.get("/dashboard/attendance-summary")
def attendance_summary(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='present'", (today,))
    present = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND is_late=true", (today,))
    late = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='absent'", (today,))
    absent = cur.fetchone()[0]

    conn.close()
    return {"present": present, "late": late, "absent": absent}


@router.get("/dashboard/department-strength")
def department_strength(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT department, COUNT(*) FROM employees
        GROUP BY department
        ORDER BY department
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"department": r[0], "count": r[1]} for r in rows]


# ---------------------- QUICK ACTIONS ----------------------
@router.post("/employees")
def add_employee(data: EmployeeCreate, user=Depends(get_current_user)):
    parts = data.full_name.strip().split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM employees WHERE emp_code=%s", (data.emp_code,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Employee code already exists")

    cur.execute("""
        INSERT INTO employees
        (emp_code, first_name, last_name, email, department, department_id, location, status,
         dob, gender, marital_status, nationality, aadhaar_ssn,
         designation, manager, date_of_joining, basic_salary, allowances)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.emp_code, first_name, last_name, data.email,
        data.department, data.department_id, data.location, data.status,
        data.dob, data.gender, data.marital_status, data.nationality,
        data.aadhaar_ssn, data.designation, data.manager,
        data.date_of_joining, data.basic_salary,
        json.dumps(data.allowances) if data.allowances else None
    ))

    conn.commit()
    conn.close()
    return {"message": "employee_added"}


@router.post("/leave/approve")
def approve_leave(data: LeaveApprove, user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE leave_requests
        SET status='Approved', approved_by=%s, approved_at=%s
        WHERE id=%s
    """, (user["email"], datetime.utcnow(), data.leave_id))
    conn.commit()
    conn.close()
    return {"message": "leave_approved"}


@router.post("/announcements")
def send_announcement(data: AnnouncementCreate, user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO announcements (title, message, created_by, created_at)
        VALUES (%s,%s,%s,%s)
    """, (data.title, data.message, user["email"], datetime.utcnow()))
    conn.commit()
    conn.close()
    return {"message": "announcement_sent"}


@router.post("/rewards")
def reward_employee(data: RewardCreate, user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO employee_rewards
        (emp_code, reward_title, reward_description, granted_by, granted_at)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        data.emp_code,
        data.reward_title,
        data.reward_description,
        user["email"],
        datetime.utcnow()
    ))
    conn.commit()
    conn.close()
    return {"message": "reward_granted"}
