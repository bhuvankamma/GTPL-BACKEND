import psycopg2
import os
import logging
from fastapi import HTTPException

# Set up logging
logger = logging.getLogger(__name__)

# --------------------------------------------------
# DB CONFIG (Uses .env variables with local fallbacks)
# --------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "hrms_crm")
DB_USER = os.getenv("DB_USER", "hrms_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Loveudad43#")

def get_connection():
    """
    Create and return a psycopg2 connection.
    """
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
    except Exception as e:
        logger.error(f"DB ERROR: {e}")
        return None

def get_cursor():
    """
    Returns (conn, cursor). Caller must close both.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn, conn.cursor()

def get_db():
    """
    FastAPI dependency for DB access (psycopg2-based)
    Used for local development/Bhavani's routes.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()

# ==================================================
# ✅ COMPATIBILITY HELPERS FOR AUTH / ADMIN MODULES
# ==================================================

def get_db_conn():
    """
    Compatibility helper for older auth/admin code.
    Returns a psycopg2 connection only.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn