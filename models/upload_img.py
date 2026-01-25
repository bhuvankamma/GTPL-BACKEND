from database_B import get_db

def ensure_tables():
    conn = get_db()
    cur = conn.cursor()

    # employees table (already exists – just reference)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_code VARCHAR(64) PRIMARY KEY
        );
    """)

    # upload_take table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS upload_take (
            id SERIAL PRIMARY KEY,
            emp_code VARCHAR(64),
            filename VARCHAR(255),
            content_type VARCHAR(127),
            image_data BYTEA,
            s3_key VARCHAR(1024),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
