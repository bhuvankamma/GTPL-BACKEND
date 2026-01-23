def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            category TEXT,
            priority TEXT,
            status TEXT,
            emp_code TEXT,
            employee_name TEXT,
            employee_department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            assigned_agent_emp_code TEXT,
            resolved_at TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_history (
            history_id BIGSERIAL PRIMARY KEY,
            ticket_id TEXT,
            action TEXT,
            old_value TEXT,
            new_value TEXT,
            updated_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
