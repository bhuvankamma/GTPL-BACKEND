from database import get_db

def get_employee_rewards(emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.id AS record_id,
            r.emp_code,
            r.reward_type,

            CASE
                WHEN r.reward_type = 'BONUS' THEN b.bonus_name
                WHEN r.reward_type = 'INCENTIVE' THEN i.incentive_name
            END AS title,

            r.recommended_amount AS amount,
            r.admin_action_at AS date_disbursed,
            EXTRACT(YEAR FROM r.admin_action_at)::int AS payment_year,
            r.admin_action_note AS official_note

        FROM employee_reward_recommendations r

        LEFT JOIN bonus_rules b
            ON r.reward_type = 'BONUS'
           AND r.reward_rule_id = b.id

        LEFT JOIN incentive_rules i
            ON r.reward_type = 'INCENTIVE'
           AND r.reward_rule_id = i.id

        WHERE r.emp_code = %s
          AND r.status = 'APPROVED'

        ORDER BY r.admin_action_at DESC
    """, (emp_code,))

    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in rows]


def get_employee_reward_insights(emp_code: str, view: str):
    conn = get_db()
    cur = conn.cursor()

    # 📊 Monthly Bar Chart
    if view == "monthly":
        cur.execute("""
            SELECT
                TO_CHAR(r.admin_action_at, 'Mon') AS month,
                EXTRACT(MONTH FROM r.admin_action_at) AS month_no,
                r.reward_type,
                SUM(r.recommended_amount) AS total
            FROM employee_reward_recommendations r
            WHERE r.emp_code = %s
              AND r.status = 'APPROVED'
            GROUP BY month, month_no, r.reward_type
            ORDER BY month_no
        """, (emp_code,))

        rows = cur.fetchall()
        result = {}

        for month, _, reward_type, total in rows:
            result.setdefault(month, {})[reward_type] = float(total)

        return [{"month": m, **v} for m, v in result.items()]

    # 🥧 Pie / Category View
    cur.execute("""
        SELECT
            CASE
                WHEN r.reward_type = 'BONUS' THEN b.bonus_name
                WHEN r.reward_type = 'INCENTIVE' THEN i.incentive_name
            END AS label,
            SUM(r.recommended_amount) AS total
        FROM employee_reward_recommendations r

        LEFT JOIN bonus_rules b
            ON r.reward_type = 'BONUS'
           AND r.reward_rule_id = b.id

        LEFT JOIN incentive_rules i
            ON r.reward_type = 'INCENTIVE'
           AND r.reward_rule_id = i.id

        WHERE r.emp_code = %s
          AND r.status = 'APPROVED'
        GROUP BY label
    """, (emp_code,))

    return [{"label": r[0], "total": float(r[1])} for r in cur.fetchall()]
