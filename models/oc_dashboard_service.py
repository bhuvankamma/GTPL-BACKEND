from database_B import get_connection


def fetch_one(sql: str, params: tuple = ()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    value = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return value


def get_dashboard_counts():

    # ---------------- SUMMARY COUNTS ---------------- #

    total_headcount = fetch_one(
        "SELECT COUNT(*) FROM employees"
    )

    open_requests = fetch_one(
        "SELECT COUNT(*) FROM tickets WHERE status = %s",
        ("open",)
    )

    pending_leaves = fetch_one(
        "SELECT COUNT(*) FROM leave_request WHERE status = %s",
        ("pending",)
    )

    monthly_hires = fetch_one(
        """
        SELECT COUNT(*)
        FROM onboarding_tokens
        WHERE DATE_TRUNC('month', created_at)
              = DATE_TRUNC('month', CURRENT_DATE)
        """
    )

    # ---------------- CRITICAL ALERTS ---------------- #

    # IT Alerts → service_configs
    it_alerts = fetch_one(
        "SELECT COUNT(*) FROM service_configs WHERE active = true"
    )

    # Finance Alerts → reimbursements
    reimbursement_pending = fetch_one(
        "SELECT COUNT(*) FROM reimbursements WHERE status = %s",
        ("pending",)
    )

    critical_approvals = it_alerts + reimbursement_pending

    return {
        "summary": {
            "total_headcount": total_headcount,
            "open_requests": open_requests,
            "pending_leaves": pending_leaves,
            "monthly_hires": monthly_hires,
            "critical_approvals": critical_approvals
        }
    }


def fetch_one(sql: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    val = cur.fetchone()[0]
    cur.close()
    conn.close()
    return val


def fetch_all(sql: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_dashboard_counts():
    total_headcount = fetch_one("SELECT COUNT(*) FROM employees")
    open_requests = fetch_one(
        "SELECT COUNT(*) FROM tickets WHERE status = %s", ("open",)
    )
    pending_leaves = fetch_one(
        "SELECT COUNT(*) FROM leave_request WHERE status = %s", ("pending",)
    )
    monthly_hires = fetch_one(
        """
        SELECT COUNT(*)
        FROM onboarding_tokens
        WHERE DATE_TRUNC('month', created_at)
              = DATE_TRUNC('month', CURRENT_DATE)
        """
    )

    it_alerts = fetch_one(
        "SELECT COUNT(*) FROM service_configs WHERE active = true"
    )

    reimbursement_pending = fetch_one(
        "SELECT COUNT(*) FROM reimbursements WHERE status = %s",
        ("pending",)
    )

    critical_approvals = it_alerts + reimbursement_pending

    return {
        "summary": {
            "total_headcount": total_headcount,
            "open_requests": open_requests,
            "pending_leaves": pending_leaves,
            "monthly_hires": monthly_hires,
            "critical_approvals": critical_approvals
        }
    }


# ---------------- NEW PART ---------------- #

def get_weekly_attendance_trend():
    rows = fetch_all(
        """
        WITH latest_week AS (
            SELECT DATE_TRUNC('week', MAX(date)) AS week_start
            FROM attendance
        )
        SELECT
            TO_CHAR(a.date, 'Dy') AS day,
            ROUND(
                (AVG(LEAST(a.work_hours / 8.0, 1)) * 100)::numeric,
                2
            ) AS attendance_percentage
        FROM attendance a
        JOIN latest_week lw
          ON a.date >= lw.week_start
         AND a.date < lw.week_start + INTERVAL '5 days'
        WHERE a.work_hours IS NOT NULL
        GROUP BY a.date
        ORDER BY a.date;
        """
    )

    return [
        {
            "day": row[0],
            "percentage": float(row[1])
        }
        for row in rows
    ]



def get_upcoming_hr_events():
    rows = fetch_all(
        """
        SELECT title, date, holiday_type
        FROM holidays
        WHERE is_active = true
          AND date >= CURRENT_DATE
        ORDER BY date
        LIMIT 5
        """
    )

    return [
        {
            "title": row[0],
            "date": row[1].strftime("%d %b"),
            "type": row[2]
        }
        for row in rows
    ]
