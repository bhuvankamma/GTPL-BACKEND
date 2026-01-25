from fastapi import APIRouter, HTTPException
from database_attendance import get_db
from schemas.schemas_attendance import RejectReasonSchema
from uuid import UUID

router = APIRouter(tags=["Manager"])


# --------------------------------------------------
# VIEW PENDING REQUESTS
# --------------------------------------------------
@router.get("/manager/requests")
def manager_requests(manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ar.*
        FROM approval_requests ar
        JOIN employees e
          ON ar.emp_code = e.emp_code
        WHERE ar.status = 'PENDING_MANAGER'
          AND e.reporting_manager_emp_code = %s
        ORDER BY ar.created_at DESC
    """, (manager_emp_code,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# --------------------------------------------------
# MANAGER APPROVE
# --------------------------------------------------
@router.post("/manager/requests/{request_id}/approve")
def manager_approve(request_id: UUID, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE approval_requests ar
        SET status = 'MANAGER_APPROVED',
            manager_id = %s,
            manager_action_at = NOW()
        FROM employees e
        WHERE ar.id = %s
          AND ar.status = 'PENDING_MANAGER'
          AND ar.emp_code = e.emp_code
          AND e.reporting_manager_emp_code = %s
    """, (manager_emp_code, request_id, manager_emp_code))

    if cur.rowcount == 0:
        raise HTTPException(400, "Invalid request state")

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Approved and sent to Admin"}


# --------------------------------------------------
# MANAGER REJECT (WITH REASON)
# --------------------------------------------------
@router.post("/manager/requests/{request_id}/reject")
def manager_reject(
    request_id: UUID,
    manager_emp_code: str,
    data: RejectReasonSchema
):
    conn = get_db()
    cur = conn.cursor()

    # Validate ownership
    cur.execute("""
        SELECT ar.request_type, ar.entity_id
        FROM approval_requests ar
        JOIN employees e ON ar.emp_code = e.emp_code
        WHERE ar.id = %s
          AND ar.status = 'PENDING_MANAGER'
          AND e.reporting_manager_emp_code = %s
    """, (request_id, manager_emp_code))

    row = cur.fetchone()
    if not row:
        raise HTTPException(400, "Invalid request state")

    request_type, entity_id = row

    # Reject
    cur.execute("""
        UPDATE approval_requests
        SET status = 'MANAGER_REJECTED',
            manager_id = %s,
            manager_reason = %s,
            manager_action_at = NOW()
        WHERE id = %s
    """, (manager_emp_code, data.reason, request_id))

    # Feature rollback only where needed
    if request_type == "ATTENDANCE_CORRECTION":
        cur.execute("""
            UPDATE attendance_corrections
            SET status = 'REJECTED'
            WHERE id = %s
        """, (entity_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Request rejected by Manager"}
