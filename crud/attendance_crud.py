from database_attendance import get_db
from datetime import datetime, date
from fastapi import HTTPException
from uuid import UUID
# ==================================================
# TIME HELPERS
# ==================================================

def minutes_diff(dt1: datetime, dt2: datetime) -> int:
    return int((dt1 - dt2).total_seconds() // 60)


# ==================================================
# CALENDAR HELPERS (USES EXISTING CURSOR)
# ==================================================

def is_holiday(cur, check_date: date) -> bool:
    cur.execute(
        "SELECT 1 FROM holiday WHERE date = %s",
        (check_date,)
    )
    return cur.fetchone() is not None


def is_weekly_off(cur, check_date: date) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM weekly_off
        WHERE day_of_week = %s
          AND is_active = TRUE
        """,
        (check_date.weekday(),)
    )
    return cur.fetchone() is not None


# ==================================================
# SHIFT HELPERS
# ==================================================

def get_employee_shift(cur, emp_code: str, check_date: date):
    cur.execute("""
        SELECT s.start_time, s.end_time
        FROM employee_shifts es
        JOIN shifts s ON s.id = es.shift_id
        WHERE es.emp_code = %s
          AND %s BETWEEN es.effective_from AND es.effective_to
    """, (emp_code, check_date))

    return cur.fetchone()

def request_leave(
    emp_code: str,
    leave_type_code: str,   # ✅ SL / CL / AL / OL
    from_date: date,
    to_date: date,
    reason: str,
    partial_mode: str | None = "full"
):
    conn = get_db()
    cur = conn.cursor()

    try:
        # --------------------------------------------------
        # 1️⃣ BASIC VALIDATION
        # --------------------------------------------------
        if partial_mode == "half" and from_date != to_date:
            raise HTTPException(400, "Half-day leave allowed only for single day")

        # --------------------------------------------------
        # 2️⃣ FETCH LEAVE TYPE UUID USING CODE
        # --------------------------------------------------
        cur.execute("""
            SELECT id
            FROM leave_type
            WHERE code = %s
              AND code != 'LOP'
        """, (leave_type_code,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(400, "Invalid leave type")

        leave_type_id = row[0]  # ✅ UUID

        # --------------------------------------------------
        # 3️⃣ CALCULATE LEAVE DAYS
        # --------------------------------------------------
        total_days = (
            0.5 if partial_mode == "half"
            else (to_date - from_date).days + 1
        )
        year = from_date.year

        # --------------------------------------------------
        # 4️⃣ LEAVE BALANCE CHECK
        # --------------------------------------------------
        cur.execute("""
            SELECT balance
            FROM leave_balance
            WHERE emp_code = %s
              AND leave_type_id = %s
              AND year = %s
        """, (emp_code, leave_type_id, year))

        bal = cur.fetchone()
        if not bal or bal[0] < total_days:
            raise HTTPException(400, "Insufficient leave balance")

        # --------------------------------------------------
        # 5️⃣ FETCH REPORTING MANAGER
        # --------------------------------------------------
        cur.execute("""
            SELECT reporting_manager_emp_code
            FROM employees
            WHERE emp_code = %s
        """, (emp_code,))

        row = cur.fetchone()
        if not row or not row[0]:
            raise HTTPException(400, "Reporting manager not assigned")

        manager_emp_code = row[0]

        # --------------------------------------------------
        # 6️⃣ INSERT INTO leave_requests (✅ CORRECT TABLE)
        # --------------------------------------------------
        cur.execute("""
            INSERT INTO leave_requests (
                emp_code,
                leave_type_id,
                start_date,
                end_date,
                partial_mode,
                reason,
                status,
                created_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,'PENDING',NOW())
            RETURNING int_id, id
        """, (
            emp_code,
            leave_type_id,
            from_date,
            to_date,
            partial_mode,
            reason
        ))

        int_id, leave_uuid = cur.fetchone()

        # --------------------------------------------------
        # 7️⃣ CREATE APPROVAL REQUEST (USES int_id)
        # --------------------------------------------------
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
            int_id,
            emp_code,
            manager_emp_code,
            reason
        ))

        conn.commit()

        return {
            "leave_id": str(leave_uuid),
            "message": "Leave request submitted successfully"
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()

# ==================================================
# ATTENDANCE FINALIZATION CHECK
# ==================================================

def is_attendance_finalized(cur, check_date: date) -> bool:
    cur.execute("""
        SELECT 1
        FROM attendance
        WHERE date = %s
          AND finalized = TRUE
        LIMIT 1
    """, (check_date,))
    return cur.fetchone() is not None
