import os
import jwt
from datetime import datetime, timedelta, date
from typing import Optional, List

import pg8000
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256

# =================================================
# LOAD ENV & CONFIG
# =================================================
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "4718529630abcdef4718529630abcdef")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

app = FastAPI(title="HRMS & Asset Management API - DEV MODE")

# Enable CORS so your React frontend can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================
# DATABASE CONNECTION
# =================================================
def get_connection():
    try:
        return pg8000.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print(f"CRITICAL: Database Connection Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# =================================================
# MODELS
# =================================================
class LoginRequest(BaseModel):
    email: str
    password: str

class Asset(BaseModel):
    name: str
    category: str
    serial_number: str
    status: str = "Available"

# =================================================
# AUTH HELPERS (Development Bypass Mode)
# =================================================
def get_current_user(authorization: Optional[str] = Header(None)):
    """
    In DEV MODE, this returns a dummy user instead of an error if the token is missing.
    This stops the 422 and 401 errors while you build the UI.
    """
    # If no token is provided, return a mock user so the request continues
    if not authorization or "null" in authorization or "undefined" in authorization:
        return {"user_id": 0, "email": "dev_user@example.com", "role": "admin"}

    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        # Return mock user even on bad/expired tokens during development
        return {"user_id": 0, "email": "dev_user@example.com", "role": "admin"}

# =================================================
# AUTH ROUTES
# =================================================
@app.post("/auth/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, email, password_hash, role FROM users WHERE email=%s", (data.email,))
    row = cur.fetchone()
    conn.close()

    if row and pbkdf2_sha256.verify(data.password, row[2]):
        token = jwt.encode({
            "user_id": row[0], 
            "email": row[1], 
            "role": row[3],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        }, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return {"token": token, "expires_in_hours": JWT_EXPIRE_HOURS}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# =================================================
# ASSET MANAGEMENT ROUTES
# =================================================
@app.get("/assets")
def get_assets(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, category, serial_number, status FROM assets")
    rows = cur.fetchall()
    conn.close()
    # If table is empty, returns [], preventing .map() crashes
    return [{"id": r[0], "name": r[1], "category": r[2], "serial_number": r[3], "status": r[4]} for r in rows]

@app.post("/assets", status_code=201)
def add_asset(asset: Asset, user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO assets (name, category, serial_number, status) VALUES (%s, %s, %s, %s)",
        (asset.name, asset.category, asset.serial_number, asset.status)
    )
    conn.commit()
    conn.close()
    return {"message": "Asset added successfully"}

# =================================================
# HR DASHBOARD ROUTES
# =================================================
@app.get("/dashboard/total-employees")
def total_employees(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees")
    result = cur.fetchone()
    count = result[0] if result else 0
    conn.close()
    return {"total_employees": count}

@app.get("/dashboard/present-today")
def present_today(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='present'", (today,))
    result = cur.fetchone()
    count = result[0] if result else 0
    conn.close()
    return {"present_today": count}

@app.get("/dashboard/on-leave")
def on_leave(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM leave_requests WHERE %s BETWEEN start_date AND end_date AND status='Approved'", (today,))
    result = cur.fetchone()
    count = result[0] if result else 0
    conn.close()
    return {"on_leave": count}

@app.get("/dashboard/attendance-summary")
def attendance_summary(user=Depends(get_current_user)):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='present'", (today,))
    p_res = cur.fetchone()
    present = p_res[0] if p_res else 0
    
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND is_late=true", (today,))
    l_res = cur.fetchone()
    late = l_res[0] if l_res else 0
    
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='absent'", (today,))
    a_res = cur.fetchone()
    absent = a_res[0] if a_res else 0
    
    conn.close()
    return {"present": present, "late": late, "absent": absent}

@app.get("/dashboard/department-strength")
def department_strength(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return []
    return [{"department": r[0], "count": r[1]} for r in rows]