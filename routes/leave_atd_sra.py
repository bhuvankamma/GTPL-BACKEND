from fastapi import APIRouter, HTTPException
from schemas.schemas_attendance import LeaveRequestSchema
from database_attendance import get_db

router = APIRouter(prefix="/leave", tags=["Leave"])


# --------------------------------------------------
# EMPLOYEE — APPLY LEAVE
# --------------------------------------------------
@router.post("/request")
def api_leave(emp_code: str, data: LeaveRequestSchema):
    conn = get_db()
    cur = conn.cursor()

    try:
        # 1️⃣ Insert leave request
        cur.execute("""
            INSERT INTO leave_requests (
                emp_code,
                leave_type,
                start_date,
                end_date,
                reason,
                status,
                applied_at
            )
            VALUES (%s,%s,%s,%s,%s,'PENDING',NOW())
            RETURNING id
        """, (
            emp_code,
            data.leave_type_code,
            data.from_date,
            data.to_date,
            data.reason
        ))

        leave_id = cur.fetchone()[0]

        # 2️⃣ Fetch reporting manager
        cur.execute("""
            SELECT reporting_manager_emp_code
            FROM employees
            WHERE emp_code = %s
        """, (emp_code,))
        row = cur.fetchone()

        if not row or not row[0]:
            raise HTTPException(400, "Reporting manager not assigned")

        manager_emp_code = row[0]

        # 3️⃣ CREATE APPROVAL REQUEST (THIS WAS MISSING ❗)
        cur.execute("""
            INSERT INTO approval_requests (
                request_type,
                entity_id,
                emp_code,
                manager_id,
                status,
                employee_reason,
                created_at
            )
            VALUES (
                'LEAVE',
                %s,
                %s,
                %s,
                'PENDING_MANAGER',
                %s,
                NOW()
            )
        """, (
            leave_id,
            emp_code,
            manager_emp_code,
            data.reason
        ))

        conn.commit()

        return {"message": "Leave request sent to manager"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))

    finally:
        cur.close()
        conn.close()
