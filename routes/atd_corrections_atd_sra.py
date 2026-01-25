from fastapi import APIRouter, Header, HTTPException
from database_attendance import get_db
from schemas.schemas_attendance import AttendanceCorrectionRequestSchema

router = APIRouter(
    prefix="/attendance/corrections",
    tags=["Attendance Corrections"]
)

# =====================================================
# EMPLOYEE — SUBMIT ATTENDANCE CORRECTION
# =====================================================
@router.post("")
def submit_correction(
    data: AttendanceCorrectionRequestSchema,
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ Attendance must exist
    cur.execute("""
        SELECT correction_locked
        FROM attendance
        WHERE emp_code=%s AND date=%s
    """, (x_emp_code, data.attendance_date))

    row = cur.fetchone()
    if not row:
        raise HTTPException(400, "Attendance record not found")

    if row[0]:
        raise HTTPException(400, "Attendance correction is locked")

    # 2️⃣ Insert or update correction
    cur.execute("""
        INSERT INTO attendance_corrections (
            emp_code,
            date,
            correction_type,
            correct_in_time,
            correct_out_time,
            reason,
            status,
            applied_by,
            applied_at
        )
        VALUES (
            %s,%s,%s,%s,%s,%s,
            'PENDING_MANAGER',
            %s,
            NOW()
        )
        ON CONFLICT (emp_code, date)
        DO UPDATE SET
            correction_type = EXCLUDED.correction_type,
            correct_in_time = EXCLUDED.correct_in_time,
            correct_out_time = EXCLUDED.correct_out_time,
            reason = EXCLUDED.reason,
            status = 'PENDING_MANAGER',
            applied_at = NOW()
        RETURNING id
    """, (
        x_emp_code,
        data.attendance_date,
        data.correction_type,
        data.corrected_in,
        data.corrected_out,
        data.reason,
        x_emp_code
    ))

    correction_id = cur.fetchone()[0]

    # 3️⃣ Remove old pending approval (safety)
    cur.execute("""
        DELETE FROM approval_requests
        WHERE request_type='ATTENDANCE_CORRECTION'
          AND entity_id=%s
          AND status='PENDING_MANAGER'
    """, (correction_id,))

    # 4️⃣ Create approval request (ONLY PLACE)
    cur.execute("""
        INSERT INTO approval_requests (
            request_type,
            entity_id,
            emp_code,
            status,
            employee_reason,
            created_at
        )
        VALUES (
            'ATTENDANCE_CORRECTION',
            %s,
            %s,
            'PENDING_MANAGER',
            %s,
            NOW()
        )
    """, (
        correction_id,
        x_emp_code,
        data.reason
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Attendance correction sent to manager"}


# =====================================================
# EMPLOYEE — VIEW OWN CORRECTIONS
# =====================================================
@router.get("/my")
def my_corrections(
    x_emp_code: str = Header(..., alias="x-emp-code")
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM attendance_corrections
        WHERE applied_by=%s
        ORDER BY applied_at DESC
    """, (x_emp_code,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
