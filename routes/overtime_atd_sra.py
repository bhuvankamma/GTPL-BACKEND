from fastapi import APIRouter, Header, HTTPException
from database_attendance import get_db
from schemas.schemas_attendance import OvertimeCreate, ManagerOvertimeReject

router = APIRouter(
    prefix="/overtime",
    tags=["Overtime"]
)

# =====================================================
# 1️⃣ EMPLOYEE — SUBMIT OVERTIME
# =====================================================
@router.post("")
def submit_overtime(
    data: OvertimeCreate,
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    try:
        # Get reporting manager EMP CODE
        cur.execute("""
            SELECT reporting_manager_emp_code
            FROM employees
            WHERE emp_code = %s
        """, (x_emp_code,))
        row = cur.fetchone()

        if not row or not row[0]:
            raise HTTPException(400, "Reporting manager not assigned")

        manager_code = row[0]

        # Insert overtime request
        cur.execute("""
            INSERT INTO overtime_requests (
                emp_code,
                date,
                hours,
                reason,
                status,
                manager_code,
                created_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                'PENDING_MANAGER',
                %s,
                NOW()
            )
        """, (
            x_emp_code,
            data.date,
            data.hours,
            data.reason,
            manager_code
        ))

        conn.commit()
        return {"message": "Overtime request submitted to manager"}

    finally:
        cur.close()
        conn.close()


# =====================================================
# 2️⃣ MANAGER — VIEW REQUESTS
# =====================================================
@router.get("/manager")
def manager_overtime_requests(
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM overtime_requests
        WHERE manager_code = %s
          AND status = 'PENDING_MANAGER'
        ORDER BY created_at DESC
    """, (x_emp_code,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# 3️⃣ MANAGER — APPROVE
# =====================================================
@router.post("/{request_id}/approve")
def approve_overtime(
    request_id: int,
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE overtime_requests
        SET status = 'APPROVED',
            manager_action_at = NOW()
        WHERE id = %s
          AND manager_code = %s
          AND status = 'PENDING_MANAGER'
    """, (request_id, x_emp_code))

    if cur.rowcount == 0:
        raise HTTPException(400, "Invalid request or already processed")

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Overtime approved"}


# =====================================================
# 4️⃣ MANAGER — REJECT (WITH REASON)
# =====================================================
@router.post("/{request_id}/reject")
def reject_overtime(
    request_id: int,
    data: ManagerOvertimeReject,
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE overtime_requests
        SET status = 'REJECTED',
            manager_reason = %s,
            manager_action_at = NOW()
        WHERE id = %s
          AND manager_code = %s
          AND status = 'PENDING_MANAGER'
    """, (data.reason, request_id, x_emp_code))

    if cur.rowcount == 0:
        raise HTTPException(400, "Invalid request or already processed")

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Overtime rejected"}


# =====================================================
# 5️⃣ EMPLOYEE — VIEW OWN OVERTIME
# =====================================================
@router.get("/my")
def my_overtime_requests(
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM overtime_requests
        WHERE emp_code = %s
        ORDER BY created_at DESC
    """, (x_emp_code,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
