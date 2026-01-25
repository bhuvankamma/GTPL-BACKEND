from fastapi import APIRouter, HTTPException, Header
from datetime import date
from database_attendance import get_db
from schemas.schemas_attendance import TimesheetEditRequestSchema

router = APIRouter(prefix="/timesheet", tags=["Timesheet"])


# ==================================================
# 1️⃣ SUBMIT TIMESHEET (EMPLOYEE → MANAGER)
# ==================================================
@router.post("/submit")
def submit_timesheet(emp_code: str, week_start: date):
    conn = get_db()
    cur = conn.cursor()

    try:
        # Update timesheet week
        cur.execute("""
            UPDATE timesheet_weeks
            SET status = 'SUBMITTED',
                locked = TRUE
            WHERE emp_code = %s
              AND week_start = %s
              AND status = 'DRAFT'
            RETURNING id
        """, (emp_code, week_start))

        row = cur.fetchone()
        if not row:
            raise HTTPException(400, "Timesheet not found or already submitted")

        timesheet_id = row[0]

        # Fetch reporting manager
        cur.execute("""
            SELECT reporting_manager_emp_code
            FROM employees
            WHERE emp_code = %s
        """, (emp_code,))
        mgr = cur.fetchone()

        if not mgr or not mgr[0]:
            raise HTTPException(400, "Reporting manager not assigned")

        manager_emp_code = mgr[0]

        # Create approval request
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
                'TIMESHEET',
                %s,
                %s,
                %s,
                'PENDING_MANAGER',
                'Weekly timesheet submitted',
                NOW()
            )
        """, (timesheet_id, emp_code, manager_emp_code))

        conn.commit()
        return {"message": "Timesheet submitted successfully"}

    finally:
        cur.close()
        conn.close()


# ==================================================
# 2️⃣ REQUEST EDIT FOR LOCKED WEEK (EMPLOYEE)
# ==================================================
@router.post("/request-edit")
def request_timesheet_edit(
    week_id: int,
    emp_code: str,
    body: TimesheetEditRequestSchema
):
    conn = get_db()
    cur = conn.cursor()

    try:
        # Validate locked week
        cur.execute("""
            SELECT 1
            FROM timesheet_weeks
            WHERE id = %s
              AND emp_code = %s
              AND locked = TRUE
        """, (week_id, emp_code))

        if not cur.fetchone():
            raise HTTPException(400, "Locked timesheet not found")

        # Prevent duplicate pending edit request
        cur.execute("""
            SELECT 1
            FROM timesheet_edit_requests
            WHERE week_id = %s
              AND manager_status = 'PENDING'
        """, (week_id,))

        if cur.fetchone():
            raise HTTPException(400, "Edit request already pending")

        # Insert edit request (emp_code based ✅)
        cur.execute("""
            INSERT INTO timesheet_edit_requests (
                week_id,
                emp_code,
                reason,
                status,
                manager_status,
                created_at
            )
            VALUES (
                %s,
                %s,
                %s,
                'PENDING',
                'PENDING',
                NOW()
            )
            RETURNING id
        """, (week_id, emp_code, body.reason))

        edit_request_id = cur.fetchone()[0]

        # Fetch reporting manager
        cur.execute("""
            SELECT reporting_manager_emp_code
            FROM employees
            WHERE emp_code = %s
        """, (emp_code,))
        mgr = cur.fetchone()

        if not mgr or not mgr[0]:
            raise HTTPException(400, "Reporting manager not assigned")

        manager_emp_code = mgr[0]

        # Create approval request
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
                'TIMESHEET_EDIT',
                %s,
                %s,
                %s,
                'PENDING_MANAGER',
                %s,
                NOW()
            )
        """, (
            edit_request_id,
            emp_code,
            manager_emp_code,
            body.reason
        ))

        conn.commit()
        return {"message": "Timesheet edit request sent to manager"}

    finally:
        cur.close()
        conn.close()


# ==================================================
# 3️⃣ EMPLOYEE — VIEW OWN EDIT REQUESTS
# ==================================================
@router.get("/edit-requests/my")
def my_timesheet_edit_requests(
    emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM timesheet_edit_requests
        WHERE emp_code = %s
        ORDER BY created_at DESC
    """, (emp_code,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
