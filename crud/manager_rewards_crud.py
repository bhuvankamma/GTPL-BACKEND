from database import get_db


def create_reward_recommendation(data, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO employee_reward_recommendations
        (emp_code, reward_type, reward_rule_id,
         recommended_by, recommended_amount, recommendation_note)
        VALUES (%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        data.emp_code,
        data.reward_type,
        data.reward_rule_id,
        manager_emp_code,
        data.amount,
        data.note
    ))

    row = cur.fetchone()
    conn.commit()

    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))
