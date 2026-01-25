from sqlalchemy import text
from sqlalchemy.orm import Session


def get_summary(db: Session):
    result = db.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE LOWER(status) = 'open') AS open_tickets,
                COUNT(*) FILTER (
                    WHERE LOWER(status) IN ('in_progress','in progress')
                ) AS in_progress,
                COUNT(*) FILTER (
                    WHERE LOWER(status) = 'resolved'
                    AND DATE(resolved_at) = CURRENT_DATE
                ) AS resolved_today
            FROM tickets;
        """)
    ).first()

    return {
        "open_tickets": result[0],
        "in_progress": result[1],
        "resolved_today": result[2],
    }


def get_active_tickets(
    db: Session,
    priority: str | None = None,
    search: str | None = None
):
    query = """
        SELECT
            t.ticket_id,
            t.title,
            t.priority,
            CONCAT(u.first_name,' ',u.last_name) AS assigned_to,
            t.status
        FROM tickets t
        LEFT JOIN users u
            ON t.assigned_agent_emp_code = u.emp_code
        WHERE 1=1
    """

    params = {}

    # Priority filter
    if priority and priority.lower() != "all":
        query += " AND LOWER(t.priority) = :priority"
        params["priority"] = priority.lower()

    # Search by title
    if search:
        query += " AND LOWER(t.title) LIKE :search"
        params["search"] = f"%{search.lower()}%"

    query += " ORDER BY t.created_at DESC LIMIT 100"

    rows = db.execute(text(query), params).all()

    return [
        {
            "ticket_id": r[0],
            "title": r[1],
            "priority": r[2],
            "assigned_to": r[3],
            "status": r[4],
        }
        for r in rows
    ]


def get_team_load(db: Session):
    rows = db.execute(
        text("""
            SELECT
                CONCAT(u.first_name,' ',u.last_name) AS name,
                ROUND(
                    100.0 * COUNT(t.ticket_id)
                    FILTER (WHERE LOWER(t.status) NOT IN ('resolved','closed'))
                    / NULLIF(COUNT(t.ticket_id),0)
                ) AS load_percent
            FROM users u
            LEFT JOIN tickets t
                ON u.emp_code = t.assigned_agent_emp_code
            WHERE u.department = 'HR'
            GROUP BY u.first_name,u.last_name
            ORDER BY 1;
        """)
    ).all()

    return [
        {"name": r[0], "load_percent": int(r[1] or 0)}
        for r in rows
    ]


def get_categories(db: Session):
    rows = db.execute(
        text("""
            SELECT category, COUNT(*)
            FROM tickets
            GROUP BY category
            ORDER BY COUNT(*) DESC;
        """)
    ).all()

    return [{"category": r[0], "count": r[1]} for r in rows]


def get_resolved_day_wise(db: Session):
    rows = db.execute(
        text("""
            SELECT DATE(resolved_at), COUNT(*)
            FROM tickets
            WHERE LOWER(status) = 'resolved'
            GROUP BY DATE(resolved_at)
            ORDER BY DATE(resolved_at);
        """)
    ).all()

    return [
        {"date": str(r[0]), "resolved_count": r[1]}
        for r in rows
    ]
