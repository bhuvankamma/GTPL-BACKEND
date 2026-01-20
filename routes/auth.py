# routes/auth.py

from fastapi import APIRouter, HTTPException
from schemas.auth import AdminRegister, LoginSchema
from db import get_db_conn
from crud.auth_crud import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/admin/register")
def admin_register(data: AdminRegister):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    conn = get_db_conn()
    cur = conn.cursor()

    try:
        # Check existing admin
        cur.execute("SELECT user_id FROM users WHERE email=%s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Admin already exists")

        # Auto-generate emp_code
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0] + 1
        emp_code = f"EMP-{str(count).zfill(3)}"

        # Insert ADMIN
        cur.execute("""
            INSERT INTO users (
                first_name,
                email,
                emp_code,
                password_hash,
                role,
                status,
                approved_by,
                approved_at
            )
            VALUES (%s,%s,%s,%s,'ADMIN','ACTIVE','SYSTEM',NOW())
        """, (
            data.full_name,
            data.email,
            emp_code,
            hash_password(data.password)
        ))

        conn.commit()

        return {
            "message": "Admin registered successfully",
            "emp_code": emp_code
        }

    finally:
        cur.close()
        conn.close()


@router.post("/login")
def login(data: LoginSchema):
    conn = get_db_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT user_id, password_hash, role, emp_code
            FROM users
            WHERE email=%s AND status='ACTIVE'
        """, (data.email,))
        user = cur.fetchone()

        if not user or not verify_password(data.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "message": "Login successful",
            "user_id": user[0],
            "role": user[2],
            "emp_code": user[3]
        }

    finally:
        cur.close()
        conn.close()
