from fastapi import APIRouter
from database_attendance import get_db
from datetime import date, timedelta

router = APIRouter(prefix="/attendance", tags=["Calendar"])

@router.get("/calendar")
def attendance_calendar(emp_code: str, month: int, year: int):
    conn = get_db()
    cur = conn.cursor()

    start = date(year, month, 1)
    end = start.replace(day=28) + timedelta(days=4)
    end = end - timedelta(days=end.day)

    cur.execute("""
        SELECT date, status
        FROM attendance
        WHERE emp_code = %s
          AND date BETWEEN %s AND %s
          AND status != 'OFF_SHIFT'
        ORDER BY date
    """, (emp_code, start, end))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {"date": r[0], "status": r[1]}
        for r in rows
    ]
