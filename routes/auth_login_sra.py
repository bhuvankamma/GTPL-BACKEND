from fastapi import APIRouter, HTTPException
from schemas.schemas_login import SuperAdminRegister, LoginSchema, SetPasswordSchema
from database_login import get_db_conn
from crud.login_crud import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/super-admin/register")
def super_admin_register(data: SuperAdminRegister):
    if data.password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM users WHERE role='SUPER_ADMIN'")
        if cur.fetchone():
            raise HTTPException(403, "Super Admin already exists")

        cur.execute("""
            INSERT INTO users (
                first_name, email, emp_code,
                password_hash, role,
                status, is_password_set
            )
            VALUES (%s,%s,'EMP-000',%s,'SUPER_ADMIN','ACTIVE',TRUE)
        """, (data.full_name, data.email, hash_password(data.password)))

    return {"message": "Super Admin registered successfully"}


@router.post("/login")
def login(data: LoginSchema):
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT password_hash, role, is_password_set
            FROM users
            WHERE email=%s AND status='ACTIVE'
        """, (data.email,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(401, "Invalid credentials")

        if not user[2]:
            raise HTTPException(403, "Password not set. Check your email.")

        if not verify_password(data.password, user[0]):
            raise HTTPException(401, "Invalid credentials")

    return {"message": "Login successful", "role": user[1]}


@router.post("/set-password")
def set_password(data: SetPasswordSchema):
    if data.new_password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id FROM users
            WHERE password_setup_token=%s
              AND password_setup_expiry > NOW()
        """, (data.token,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(400, "Invalid or expired token")

        cur.execute("""
            UPDATE users
            SET password_hash=%s,
                is_password_set=TRUE,
                password_setup_token=NULL,
                password_setup_expiry=NULL
            WHERE user_id=%s
        """, (hash_password(data.new_password), user[0]))

    return {"message": "Password set successfully"}
