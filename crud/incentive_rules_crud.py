from database import get_db
from decimal import Decimal

def create_incentive_rule(data, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO incentive_rules
        (
            incentive_code,
            incentive_name,
            percentage_value,
            per_unit_amount,
            fixed_amount,
            is_active,
            created_by
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        data.incentiveCode,
        data.incentiveName,
        Decimal(data.percentageValue) if data.percentageValue else None,
        Decimal(data.perUnitAmount) if data.perUnitAmount else None,
        Decimal(data.fixedAmount) if data.fixedAmount else None,
        data.isActive,
        manager_emp_code
    ))

    row = cur.fetchone()
    conn.commit()

    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))



# --------------------------------------------------
# LIST INCENTIVE RULES (MANAGER-WISE)
# --------------------------------------------------
def list_incentive_rules(manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                incentive_code,
                incentive_name,
                percentage_value,
                per_unit_amount,
                fixed_amount,
                is_active,
                created_by
            FROM incentive_rules
            WHERE is_active = TRUE
              AND created_by = %s
            ORDER BY incentive_name
            """,
            (manager_emp_code,)
        )

        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]

        return [dict(zip(cols, r)) for r in rows]

    finally:
        cur.close()
        conn.close()


# --------------------------------------------------
# SOFT DELETE INCENTIVE RULE
# --------------------------------------------------
def deactivate_incentive_rule(rule_id: int, manager_emp_code: str):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE incentive_rules
            SET is_active = FALSE
            WHERE id = %s
              AND created_by = %s
            """,
            (rule_id, manager_emp_code)
        )

        if cur.rowcount == 0:
            return {
                "success": False,
                "message": "Incentive rule not found or not authorized"
            }

        conn.commit()
        return {
            "success": True,
            "message": "Incentive rule deactivated successfully"
        }

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()
