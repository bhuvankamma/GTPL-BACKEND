from datetime import datetime
from fastapi import HTTPException
from database import get_db

# EMP-011- MANAGER
# EMP001 - EMPLOYEE

def list_pending_rewards():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM employee_reward_recommendations
        WHERE status = 'PENDING_ADMIN_APPROVAL'
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def admin_action_reward(rec_id: int, data):
    # TEMP MOCK (until JWT)
    current_user = {"emp_code": "ADM001", "role": "ADMIN"}

    if current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT status FROM employee_reward_recommendations WHERE id = %s",
        (rec_id,)
    )
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Reward record not found")

    if row[0] != "PENDING_ADMIN_APPROVAL":
        raise HTTPException(status_code=400, detail="Reward already processed")

    cur.execute(
        """
        UPDATE employee_reward_recommendations
        SET status=%s,
            admin_action_by=%s,
            admin_action_note=%s,
            admin_action_at=%s
        WHERE id=%s
        RETURNING *
        """,
        (
            data.status,
            current_user["emp_code"],
            data.note,
            datetime.utcnow(),
            rec_id
        )
    )

    conn.commit()
    return {"message": f"Reward {data.status}", "id": rec_id}
