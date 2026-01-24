from database_B import get_connection
from sqlalchemy import create_engine


def _rows_to_dicts(cursor, rows):
    if not rows:
        return []
    cols = [c[0] for c in cursor.description]
    return [{cols[i]: row[i] for i in range(len(cols))} for row in rows]

"""
def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql, tuple(params or []))

        if commit:
            conn.commit()

        if fetchone:
            row = cur.fetchone()
            return _rows_to_dicts(cur, [row])[0] if row else None

        if fetchall:
            return _rows_to_dicts(cur, cur.fetchall())

        return {"rowcount": cur.rowcount}

    finally:
        cur.close()
        conn.close()
"""

def list_configs(params):
    q = params.get("q", "")
    typ = params.get("type", "")
    sort = params.get("sort", "most_recent")

    order = "created_at DESC"
    if "price" in sort.lower():
        order = "price_inr DESC"
    elif "duration" in sort.lower():
        order = "duration_months DESC"

    sql = "SELECT * FROM service_configs WHERE 1=1"
    args = []

    if q:
        sql += " AND (name ILIKE %s OR coverage ILIKE %s)"
        args.extend([f"%{q}%", f"%{q}%"])

    if typ and typ.lower() != "all":
        sql += " AND type=%s"
        args.append(typ)

    sql += f" ORDER BY {order}"
    return execute_query(sql, args, fetchall=True)


def get_config(id_):
    return execute_query(
        "SELECT * FROM service_configs WHERE id=%s",
        [id_],
        fetchone=True,
    )


def create_config(data):
    return execute_query(
        """
        INSERT INTO service_configs
        (name,type,duration_months,price_inr,coverage,
         sla_response_hours,sla_resolution_hours,active)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *;
        """,
        [
            data.get("name"),
            data.get("type", "Warranty"),
            int(data.get("duration_months", 0)),
            int(data.get("price_inr", 0)),
            data.get("coverage", ""),
            int(data.get("sla_response_hours", 0)),
            int(data.get("sla_resolution_hours", 0)),
            bool(data.get("active", True)),
        ],
        fetchone=True,
        commit=True,
    )


def update_config(id_, data):
    sets, args = [], []

    for k, v in data.items():
        sets.append(f"{k}=%s")
        args.append(v)

    if not sets:
        return get_config(id_)

    args.append(id_)

    return execute_query(
        f"""
        UPDATE service_configs
        SET {', '.join(sets)}
        WHERE id=%s
        RETURNING *;
        """,
        args,
        fetchone=True,
        commit=True,
    )


def delete_config(id_):
    return execute_query(
        "DELETE FROM service_configs WHERE id=%s RETURNING id;",
        [id_],
        fetchone=True,
        commit=True,
    )


def toggle_active(id_):
    row = get_config(id_)
    if not row:
        return None

    return execute_query(
        "UPDATE service_configs SET active=%s WHERE id=%s RETURNING *;",
        [not row["active"], id_],
        fetchone=True,
        commit=True,
    )


def export_configs():
    return execute_query(
        "SELECT * FROM service_configs ORDER BY created_at DESC;",
        fetchall=True,
    )


def import_configs(records):
    out = []
    for r in records:
        if r.get("id"):
            out.append(update_config(r["id"], r))
        else:
            out.append(create_config(r))
    return out




# --------------------------------------------------
# QUERY EXECUTOR
# --------------------------------------------------
def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(params or []))

            if commit:
                conn.commit()

            if fetchone:
                row = cur.fetchone()
                return (
                    dict(zip([c[0] for c in cur.description], row))
                    if row else None
                )

            if fetchall:
                rows = cur.fetchall()
                cols = [c[0] for c in cur.description]
                return [dict(zip(cols, r)) for r in rows]

            return {"rowcount": cur.rowcount}

        finally:
            cur.close()

# --------------------------------------------------
# SAFE TABLE + FUNCTION + TRIGGER CREATION
# --------------------------------------------------
def ensure_tables():
    ddl_table = """
    CREATE TABLE IF NOT EXISTS service_configs (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        duration_months INTEGER DEFAULT 0,
        price_inr BIGINT DEFAULT 0,
        coverage TEXT,
        sla_response_hours INTEGER DEFAULT 0,
        sla_resolution_hours INTEGER DEFAULT 0,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    """

    # SAFE FUNCTION CREATION (NO OWNER CONFLICT)
    ddl_function = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
        ) THEN
            CREATE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $func$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $func$ LANGUAGE plpgsql;
        END IF;
    END;
    $$;
    """

    ddl_trigger = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trg_service_configs_updated_at'
        ) THEN
            CREATE TRIGGER trg_service_configs_updated_at
            BEFORE UPDATE ON service_configs
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        END IF;
    END;
    $$;
    """

    execute_query(ddl_table, commit=True)
    execute_query(ddl_function, commit=True)
    execute_query(ddl_trigger, commit=True)
