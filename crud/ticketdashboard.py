def get_summary(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE LOWER(status) = 'open'),
            COUNT(*) FILTER (WHERE LOWER(status) IN ('in_progress','in progress')),
            COUNT(*) FILTER (
                WHERE LOWER(status) = 'resolved'
                AND DATE(resolved_at) = CURRENT_DATE
            )
        FROM tickets;
    """)
    r = cur.fetchone()
    return {
        "open_tickets": r[0],
        "in_progress": r[1],
        "resolved_today": r[2]
    }




def get_active_tickets(conn, priority: str | None = None, search: str | None = None):
    cur = conn.cursor()

    query = """
        SELECT
            t.ticket_id,
            t.title,
            t.priority,
            CONCAT(u.first_name,' ',u.last_name),
            t.status
        FROM tickets t
        LEFT JOIN users u
            ON t.assigned_agent_emp_code = u.emp_code
        WHERE 1=1
    """

    params = []

    # Priority filter
    if priority and priority.lower() != "all":
        query += " AND LOWER(t.priority) = %s"
        params.append(priority.lower())

    # Search by title
    if search:
        query += " AND LOWER(t.title) LIKE %s"
        params.append(f"%{search.lower()}%")

    query += " ORDER BY t.created_at DESC LIMIT 100"

    cur.execute(query, params)

    return [{
        "ticket_id": r[0],
        "title": r[1],
        "priority": r[2],
        "assigned_to": r[3],
        "status": r[4]
    } for r in cur.fetchall()]


def get_team_load(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            CONCAT(u.first_name,' ',u.last_name),
            ROUND(
                100.0 * COUNT(t.ticket_id)
                FILTER (WHERE LOWER(t.status) NOT IN ('resolved','closed'))
                / NULLIF(COUNT(t.ticket_id),0)
            )
        FROM users u
        LEFT JOIN tickets t
            ON u.emp_code = t.assigned_agent_emp_code
        WHERE u.department = 'HR'
        GROUP BY u.first_name,u.last_name
        ORDER BY 1;
    """)
    return [{"name": r[0], "load_percent": int(r[1] or 0)} for r in cur.fetchall()]



def get_categories(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT category, COUNT(*)
        FROM tickets
        GROUP BY category
        ORDER BY COUNT(*) DESC;
    """)
    return [{"category": r[0], "count": r[1]} for r in cur.fetchall()]


def get_resolved_day_wise(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(resolved_at), COUNT(*)
        FROM tickets
        WHERE LOWER(status) = 'resolved'
        GROUP BY DATE(resolved_at)
        ORDER BY DATE(resolved_at);
    """)
    return [
        {"date": str(r[0]), "resolved_count": r[1]}
        for r in cur.fetchall()
    ]
