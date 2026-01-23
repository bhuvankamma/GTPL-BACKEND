import psycopg2
from fastapi import HTTPException
 
 
def get_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5432,
            database="hrms_crm",
            user="hrms_user",
            password="Loveudad43#",
            connect_timeout=5
        )
    except Exception as e:
        print("DB ERROR:", e)
        return None
 
 
def get_cursor():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn, conn.cursor()
 
 
def get_db():
    """
    FastAPI dependency for DB access (psycopg2-based)
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()
 
 
# ==================================================
# ✅ ADDED FOR AUTH / ADMIN MODULE COMPATIBILITY
# ==================================================
 
def get_db_conn():
    """
    Compatibility helper for auth/admin code.
    Returns a psycopg2 connection only.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn