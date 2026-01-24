from database_B import get_db_conn, logger

# ==================================================
# 🔥 TABLE CREATION — FULL & EXACT
# ==================================================

# ---------------- employees ----------------
CREATE_EMPLOYEES_TABLE = """
CREATE TABLE IF NOT EXISTS employees (
    emp_code VARCHAR(50) PRIMARY KEY,
    official_email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# ---------------- upload_take ----------------
CREATE_UPLOAD_TAKE_TABLE = """
CREATE TABLE IF NOT EXISTS upload_take (
    id SERIAL PRIMARY KEY,
    emp_code VARCHAR(50) NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT,
    s3_key TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
"""

# ---------------- form12bb_uploads ----------------
CREATE_FORM12BB_UPLOADS_TABLE = """
CREATE TABLE IF NOT EXISTS form12bb_uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    financial_year VARCHAR(50),
    filename VARCHAR(512),
    filepath TEXT,
    file_url TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
"""

# ---------------- declarations (FULL) ----------------
CREATE_DECLARATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS declarations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    financial_year VARCHAR(50) NOT NULL,

    current_monthly_rent NUMERIC DEFAULT 0,
    landlord_name TEXT,
    landlord_address TEXT,

    hra_amount NUMERIC DEFAULT 0,

    section_80c NUMERIC DEFAULT 0,
    section_80ccd NUMERIC DEFAULT 0,
    section_80d NUMERIC DEFAULT 0,
    section_80dd NUMERIC DEFAULT 0,
    section_80ddb NUMERIC DEFAULT 0,
    section_80e NUMERIC DEFAULT 0,
    section_80ee NUMERIC DEFAULT 0,
    section_80g NUMERIC DEFAULT 0,
    section_80u NUMERIC DEFAULT 0,
    section_80eea NUMERIC DEFAULT 0,
    section_80eeb NUMERIC DEFAULT 0,
    section_80tta NUMERIC DEFAULT 0,
    section_80ttb NUMERIC DEFAULT 0,

    home_loan_interest NUMERIC DEFAULT 0,
    lta_amount NUMERIC DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE (user_id, financial_year)
);
"""

# --------------------------------------------------
# INIT DB (CALLED ON FASTAPI STARTUP)
# --------------------------------------------------
def init_db():
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute(CREATE_EMPLOYEES_TABLE)
        cur.execute(CREATE_UPLOAD_TAKE_TABLE)
        cur.execute(CREATE_FORM12BB_UPLOADS_TABLE)
        cur.execute(CREATE_DECLARATIONS_TABLE)

        conn.commit()
        logger.info(
            "✅ Tables ensured: employees, upload_take, form12bb_uploads, declarations"
        )
    except Exception as e:
        logger.error("❌ DB init failed", exc_info=e)
    finally:
        if conn:
            conn.close()
