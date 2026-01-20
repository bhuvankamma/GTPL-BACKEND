from fastapi import APIRouter, HTTPException
from schemas.employee import CreateEmployee
from db import get_db_conn
from crud.auth_crud import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])
@router.post("/create-employee")
def create_employee(data: CreateEmployee):
    conn = get_db_conn()
    cur = conn.cursor()

    try:
        default_password = hash_password("Welcome@123")

        # Check duplicate emp_code or email
        cur.execute(
            "SELECT user_id FROM users WHERE emp_code=%s OR email=%s",
            (data.emp_code, data.email)
        )
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Employee already exists")

        # Insert into users table
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
            VALUES (%s,%s,%s,%s,%s,'ACTIVE','ADMIN',NOW())
            RETURNING user_id
        """, (
            data.full_name,
            data.email,
            data.emp_code,
            default_password,
            data.role.upper()
        ))

        # Insert into employees table
        cur.execute("""
            INSERT INTO employees (
                emp_code,
                first_name,
                department,
                employment_type,
                official_email,
                reporting_manager_emp_code
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            data.emp_code,
            data.full_name,
            data.department,
            data.employee_type.upper(),
            data.email,
            data.reporting_manager_emp_code
        ))

        conn.commit()

        return {
            "message": "Employee created successfully",
            "emp_code": data.emp_code
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

