from fastapi import APIRouter
from database_attendance import get_db
from datetime import date, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# --------------------------------------------------
# 1️⃣ Monthly Attendance Summary
# --------------------------------------------------
@router.get("/attendance-summary")
def attendance_summary(emp_code: str, month: int, year: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        WHERE emp_code = %s
          AND EXTRACT(MONTH FROM date) = %s
          AND EXTRACT(YEAR FROM date) = %s
          AND status NOT IN ('OFF_SHIFT', 'HOLIDAY')
        GROUP BY status
    """, (emp_code, month, year))

    result = dict(cur.fetchall())

    cur.close()
    conn.close()
    return result


# --------------------------------------------------
# 2️⃣ Weekly Summary (Current Week)
# --------------------------------------------------
@router.get("/weekly-summary")
def weekly_summary(emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    cur.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        WHERE emp_code = %s
          AND date BETWEEN %s AND %s
          AND status NOT IN ('OFF_SHIFT', 'HOLIDAY')
        GROUP BY status
    """, (emp_code, week_start, week_end))

    summary = dict(cur.fetchall())

    cur.close()
    conn.close()

    return {
        "week_start": week_start,
        "week_end": week_end,
        "summary": summary
    }


# --------------------------------------------------
# 3️⃣ Check-in Trends (Charts)
# --------------------------------------------------
@router.get("/checkin-trends")
def checkin_trends(emp_code: str, month: int, year: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, in_time
        FROM attendance
        WHERE emp_code = %s
          AND in_time IS NOT NULL
          AND EXTRACT(MONTH FROM date) = %s
          AND EXTRACT(YEAR FROM date) = %s
        ORDER BY date
    """, (emp_code, month, year))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "date": d.isoformat(),
            "check_in": in_time.strftime("%H:%M")
        }
        for d, in_time in rows
    ]


# --------------------------------------------------
# 4️⃣ My Exceptions (Late / Early / Half-Day)
# --------------------------------------------------
@router.get("/my-exceptions")
def my_exceptions(emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            SUM(CASE WHEN is_late THEN 1 ELSE 0 END),
            SUM(CASE WHEN is_early_leave THEN 1 ELSE 0 END),
            SUM(CASE WHEN is_half_day THEN 1 ELSE 0 END)
        FROM attendance
        WHERE emp_code = %s
          AND status NOT IN ('OFF_SHIFT', 'HOLIDAY')
    """, (emp_code,))

    late, early, half = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "late_coming": late or 0,
        "early_going": early or 0,
        "half_days": half or 0
    }
