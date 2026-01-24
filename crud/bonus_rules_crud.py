from database import get_db
from decimal import Decimal


def list_bonus_rules(manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, bonus_code, bonus_name, frequency,
               percentage_of_ctc, fixed_amount, is_active
        FROM bonus_rules
        ORDER BY bonus_name
    """)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def create_bonus_rule(data, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bonus_rules
        (bonus_code, bonus_name, frequency, percentage_of_ctc, fixed_amount, is_active)
        VALUES (%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        data.bonusCode,
        data.bonusName,
        data.frequency,
        Decimal(data.percentageOfCtc) if data.percentageOfCtc else None,
        Decimal(data.fixedAmount) if data.fixedAmount else None,
        data.isActive
    ))

    row = cur.fetchone()
    conn.commit()
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))


def update_bonus_rule(rule_id, data, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bonus_rules
        SET bonus_code = %s,
            bonus_name = %s,
            frequency = %s,
            percentage_of_ctc = %s,
            fixed_amount = %s,
            is_active = %s
        WHERE id = %s
        RETURNING *
    """, (
        data.bonusCode,
        data.bonusName,
        data.frequency,
        Decimal(data.percentageOfCtc) if data.percentageOfCtc else None,
        Decimal(data.fixedAmount) if data.fixedAmount else None,
        data.isActive,
        rule_id
    ))

    row = cur.fetchone()
    conn.commit()
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))


def delete_bonus_rule(rule_id, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM bonus_rules
        WHERE id = %s
        RETURNING id
    """, (rule_id,))

    row = cur.fetchone()
    conn.commit()
    return {"deleted_id": row[0]}
