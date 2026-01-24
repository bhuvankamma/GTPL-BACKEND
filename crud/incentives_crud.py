from database import get_db

def list_incentives(emp_code: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM incentives
        WHERE emp_code = %s
        ORDER BY created_at DESC
    """, (emp_code,))
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]
