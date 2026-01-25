from fastapi import APIRouter, HTTPException
from database_attendance import get_db
from datetime import date

router = APIRouter(prefix="/shift", tags=["Shift"])


# --------------------------------------------------
# ASSIGN SHIFT (ADMIN)
# --------------------------------------------------
@router.post("/assign")
def assign_shift(
    emp_code: str,
    shift_id: int,
    effective_from: date,
    effective_to: date | None = None
):
    if effective_to and effective_to < effective_from:
        raise HTTPException(400, "effective_to cannot be before effective_from")

    conn = get_db()
    cur = conn.cursor()

    try:
        # Validate employee exists
        cur.execute("""
            SELECT 1 FROM employees WHERE emp_code = %s
        """, (emp_code,))
        if not cur.fetchone():
            raise HTTPException(400, "Employee not found")

        # Validate shift exists
        cur.execute("""
            SELECT 1 FROM shifts WHERE id = %s
        """, (shift_id,))
        if not cur.fetchone():
            raise HTTPException(400, "Shift not found")

        # Check if shift already exists
        cur.execute("""
            SELECT 1
            FROM employee_shifts
            WHERE emp_code = %s
        """, (emp_code,))
        exists = cur.fetchone()

        if exists:
            # Update existing shift
            cur.execute("""
                UPDATE employee_shifts
                SET shift_id = %s,
                    effective_from = %s,
                    effective_to = %s
                WHERE emp_code = %s
            """, (
                shift_id,
                effective_from,
                effective_to,
                emp_code
            ))
        else:
            # Insert new shift
            cur.execute("""
                INSERT INTO employee_shifts
                (emp_code, shift_id, effective_from, effective_to)
                VALUES (%s, %s, %s, %s)
            """, (
                emp_code,
                shift_id,
                effective_from,
                effective_to
            ))

        conn.commit()
        return {"message": "Shift assigned successfully"}

    finally:
        cur.close()
        conn.close()


# --------------------------------------------------
# GET CURRENT SHIFT (EMPLOYEE)
# --------------------------------------------------
@router.get("/my")
def my_shift(emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT s.shift_name, s.start_time, s.end_time, s.break_minutes
            FROM employee_shifts es
            JOIN shifts s ON s.id = es.shift_id
            WHERE es.emp_code = %s
              AND CURRENT_DATE BETWEEN es.effective_from
                                  AND COALESCE(es.effective_to, CURRENT_DATE)
        """, (emp_code,))

        row = cur.fetchone()
        if not row:
            return {"message": "No shift assigned"}

        return {
            "shift_name": row[0],
            "start_time": str(row[1]),
            "end_time": str(row[2]),
            "break_minutes": row[3]
        }

    finally:
        cur.close()
        conn.close()
