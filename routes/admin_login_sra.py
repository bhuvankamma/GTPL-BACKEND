from fastapi import APIRouter, HTTPException
from schemas.schemas_login import CreateEmployee
from database_login import get_db_conn
from crud.login_crud import generate_password_token
from utils.email_service_login import send_password_setup_email

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/create-user")
def create_user(data: CreateEmployee):
    token, expiry = generate_password_token()

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (
                first_name, email, emp_code, role,
                status, is_password_set,
                password_setup_token, password_setup_expiry
            )
            VALUES (%s,%s,%s,%s,'ACTIVE',FALSE,%s,%s)
        """, (
            data.full_name,
            data.email,
            data.emp_code,
            data.role,
            token,
            expiry
        ))

        cur.execute("""
            INSERT INTO employees (
                emp_code, department,
                employment_type, reporting_manager_emp_code
            )
            VALUES (%s,%s,%s,%s)
        """, (
            data.emp_code,
            data.department,
            data.employee_type,
            data.reporting_manager_emp_code
        ))

    send_password_setup_email(data.email, token)
    return {"message": "User created & email sent"}
