import psycopg2
from fastapi import HTTPException

# ==================================================
# DATABASE CONFIG (MERGED)
# ==================================================
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "hrms_crm"
DB_USER = "hrms_user"
DB_PASSWORD = "Loveudad43#"
DB_TIMEOUT = 5

# ==================================================
# CONNECTION
# ==================================================
def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=DB_TIMEOUT
        )
    except Exception as e:
        print("DB CONNECTION ERROR:", e)
        return None


# ==================================================
# CURSOR (USED BY FASTAPI ROUTES)
# ==================================================
def get_cursor():
    conn = get_connection()
    if not conn:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )
    return conn, conn.cursor()
