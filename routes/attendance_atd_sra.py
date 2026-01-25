from datetime import datetime, date
from fastapi import APIRouter, HTTPException

from database_attendance import get_db
from crud.attendance_crud import (
    get_employee_shift,
    minutes_diff,
    is_attendance_finalized
)
from utils.config_attendance import (
    LATE_GRACE_MINUTES,
    EARLY_LEAVE_GRACE_MINUTES,
    HALF_DAY_LATE_THRESHOLD,
    HALF_DAY_WORK_RATIO
)

router = APIRouter(tags=["Attendance"])


# ==================================================
# CHECK-IN
# ==================================================
@router.post("/attendance/check-in")
def check_in(emp_code: str, source: str):
    conn = get_db()
    cur = conn.cursor()

    now = datetime.now()
    today = now.date()

    if is_attendance_finalized(cur, today):
        raise HTTPException(403, "Attendance finalized. Check-in not allowed")

    cur.execute("""
        SELECT 1
        FROM attendance
        WHERE emp_code = %s AND date = %s
    """, (emp_code, today))

    if cur.fetchone():
        raise HTTPException(400, "Already checked in")

    shift = get_employee_shift(cur, emp_code, today)
    if not shift:
        raise HTTPException(400, "Shift not assigned")

    shift_start, _ = shift
    shift_start_dt = datetime.combine(today, shift_start)

    late_minutes = max(0, minutes_diff(now, shift_start_dt))
    is_late = late_minutes > LATE_GRACE_MINUTES

    cur.execute("""
        INSERT INTO attendance (
            emp_code,
            date,
            in_time,
            is_late,
            late_minutes,
            status,
            source
        )
        VALUES (%s, %s, %s, %s, %s, 'PRESENT', %s)
    """, (
        emp_code,
        today,
        now,
        is_late,
        late_minutes,
        source
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Checked in successfully"}


# ==================================================
# CHECK-OUT (✅ FIXED)
# ==================================================
@router.post("/attendance/check-out")
def check_out(emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    now = datetime.now()
    today = now.date()

    if is_attendance_finalized(cur, today):
        raise HTTPException(403, "Attendance finalized. Check-out not allowed")

    cur.execute("""
        SELECT in_time, late_minutes, out_time
        FROM attendance
        WHERE emp_code = %s AND date = %s
    """, (emp_code, today))

    row = cur.fetchone()
    if not row:
        raise HTTPException(400, "Check-in not found")

    in_time, late_minutes, out_time = row
    if out_time:
        raise HTTPException(400, "Already checked out")

    shift = get_employee_shift(cur, emp_code, today)
    if not shift:
        raise HTTPException(400, "Shift not assigned")

    shift_start, shift_end = shift
    shift_start_dt = datetime.combine(today, shift_start)
    shift_end_dt = datetime.combine(today, shift_end)

    # ✅ Calculate minutes
    work_minutes = minutes_diff(now, in_time)
    shift_minutes = minutes_diff(shift_end_dt, shift_start_dt)

    # ✅ Convert to hours (DB COLUMN)
    work_hours = round(work_minutes / 60, 2)

    early_leave_minutes = max(0, minutes_diff(shift_end_dt, now))
    is_early_leave = early_leave_minutes > EARLY_LEAVE_GRACE_MINUTES

    is_half_day = (
        late_minutes >= HALF_DAY_LATE_THRESHOLD or
        work_minutes < shift_minutes * HALF_DAY_WORK_RATIO
    )

    status = "HALF_DAY" if is_half_day else "PRESENT"

    cur.execute("""
        UPDATE attendance
        SET
            out_time = %s,
            work_hours = %s,
            is_early_leave = %s,
            early_leave_minutes = %s,
            is_half_day = %s,
            status = %s
        WHERE emp_code = %s AND date = %s
    """, (
        now,
        work_hours,
        is_early_leave,
        early_leave_minutes,
        is_half_day,
        status,
        emp_code,
        today
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Checked out successfully",
        "status": status,
        "work_hours": work_hours
    }


# ==================================================
# MONTHLY ATTENDANCE SUMMARY (VIEW)
# ==================================================
@router.get("/attendance/monthly-summary")
def monthly_summary(month: date | None = None):
    conn = get_db()
    cur = conn.cursor()

    if month:
        cur.execute("""
            SELECT *
            FROM monthly_attendance_summary
            WHERE month = DATE_TRUNC('month', %s::date)
            ORDER BY emp_code
        """, (month,))
    else:
        cur.execute("""
            SELECT *
            FROM monthly_attendance_summary
            ORDER BY month DESC, emp_code
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows

# ==================================================
# MONTHLY ATTENDANCE SUMMARY (VIEW)
# ==================================================
@router.get("/attendance/monthly-summary")
def monthly_summary(month: date | None = None):
    conn = get_db()
    cur = conn.cursor()

    if month:
        cur.execute("""
            SELECT *
            FROM monthly_attendance_summary
            WHERE month = DATE_TRUNC('month', %s::date)
            ORDER BY emp_code
        """, (month,))
    else:
        cur.execute("""
            SELECT *
            FROM monthly_attendance_summary
            ORDER BY month DESC, emp_code
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows
