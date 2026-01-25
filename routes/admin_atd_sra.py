from fastapi import APIRouter, HTTPException
from datetime import timedelta
from database_attendance import get_db
from schemas.schemas_attendance import RejectReasonSchema
from crud.attendance_crud import is_holiday, is_weekly_off
from uuid import UUID

router = APIRouter(tags=["Admin"])


# --------------------------------------------------
# ADMIN — VIEW MANAGER APPROVED
# --------------------------------------------------
@router.get("/admin/requests")
def admin_requests():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM approval_requests
        WHERE status = 'MANAGER_APPROVED'
        ORDER BY manager_action_at DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# --------------------------------------------------
# ADMIN — FINAL APPROVE
# --------------------------------------------------
@router.post("/admin/requests/{request_id}/finalize")
def admin_finalize(request_id: UUID, admin_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    # Fetch request
    cur.execute("""
        SELECT request_type, entity_id
        FROM approval_requests
        WHERE id = %s
          AND status = 'MANAGER_APPROVED'
    """, (request_id,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(400, "Invalid request state")

    request_type, entity_id = row

    # --------------------------------------------------
    # APPLY FINAL EFFECT
    # --------------------------------------------------
    if request_type == "LEAVE":
        cur.execute("""
            SELECT emp_code, start_date, end_date
            FROM leave_requests
            WHERE id = %s
        """, (entity_id,))
        leave = cur.fetchone()
        if not leave:
            raise HTTPException(400, "Leave not found")

        emp_code, start, end = leave
        d = start
        while d <= end:
            if not is_holiday(cur, d) and not is_weekly_off(cur, d):
                cur.execute("""
                    INSERT INTO attendance (emp_code, date, status)
                    VALUES (%s,%s,'LEAVE')
                    ON CONFLICT (emp_code, date)
                    DO UPDATE SET status='LEAVE'
                """, (emp_code, d))
            d += timedelta(days=1)

    elif request_type == "ATTENDANCE_CORRECTION":
        # Fetch correction
        cur.execute("""
            SELECT emp_code, date, correct_in_time, correct_out_time
            FROM attendance_corrections
            WHERE id = %s
        """, (entity_id,))
        ac = cur.fetchone()
        if not ac:
            raise HTTPException(400, "Attendance correction not found")

        emp_code, att_date, cin, cout = ac

        # Apply to attendance
        cur.execute("""
            UPDATE attendance
            SET in_time = %s,
                out_time = %s,
                correction_locked = TRUE
            WHERE emp_code = %s
              AND date = %s
        """, (cin, cout, emp_code, att_date))

        # Update correction
        cur.execute("""
            UPDATE attendance_corrections
            SET status = 'APPROVED',
                approved_by = %s,
                approved_at = NOW()
            WHERE id = %s
        """, (admin_emp_code, entity_id))

    elif request_type in ("TIMESHEET", "TIMESHEET_EDIT"):
        cur.execute("""
            UPDATE timesheet_weeks
            SET locked = TRUE,
                admin_status = 'APPROVED',
                approved_by_admin = %s,
                approved_at = NOW()
            WHERE id = %s
        """, (admin_emp_code, entity_id))

    # --------------------------------------------------
    # FINAL STATUS UPDATE
    # --------------------------------------------------
    cur.execute("""
        UPDATE approval_requests
        SET status = 'ADMIN_APPROVED',
            admin_id = %s,
            admin_action_at = NOW()
        WHERE id = %s
    """, (admin_emp_code, request_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Request finalized by Admin"}


# --------------------------------------------------
# ADMIN — REJECT (WITH REASON)
# --------------------------------------------------
@router.post("/admin/requests/{request_id}/reject")
def admin_reject(
    request_id: UUID,
    admin_emp_code: str,
    data: RejectReasonSchema
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE approval_requests
        SET status = 'ADMIN_REJECTED',
            admin_id = %s,
            admin_reason = %s,
            admin_action_at = NOW()
        WHERE id = %s
          AND status = 'MANAGER_APPROVED'
    """, (admin_emp_code, data.reason, request_id))

    if cur.rowcount == 0:
        raise HTTPException(400, "Invalid request state")

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Request rejected by Admin"}
