import os
import logging
import psycopg2
from sshtunnel import SSHTunnelForwarder
from urllib.parse import quote_plus
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ==================================================
# LOGGING
# ==================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================================================
# SSH CONFIG
# ==================================================
SSH_HOST = "122.186.222.20"
SSH_PORT = 22
SSH_USER = "hrmsadmin"
SSH_PASSWORD = "Dell@123"   # 🔴 Recommend moving to .env later

# ==================================================
# DATABASE CONFIG (REMOTE POSTGRES)
# ==================================================
DB_HOST = "127.0.0.1"       # DB host inside remote server
DB_PORT = 5432
DB_USER = "hrms_user"
DB_PASSWORD = "Loveudad43#"
DB_NAME = "hrms_crm"

ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)

# ==================================================
# GLOBALS (SINGLETON)
# ==================================================
ssh_tunnel = None
engine = None
SessionLocal = None

Base = declarative_base()

# ==================================================
# SSH TUNNEL + SQLALCHEMY ENGINE (LAZY INIT)
# ==================================================
def start_ssh_tunnel():
    global ssh_tunnel, engine, SessionLocal

    if ssh_tunnel and ssh_tunnel.is_active:
        return

    logger.info("Starting SSH tunnel...")

    try:
        ssh_tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST, DB_PORT),
        )

        ssh_tunnel.start()

        logger.info(
            f"SSH tunnel established on localhost:{ssh_tunnel.local_bind_port}"
        )

        DATABASE_URL = (
            f"postgresql+psycopg2://{DB_USER}:{ENCODED_DB_PASSWORD}"
            f"@127.0.0.1:{ssh_tunnel.local_bind_port}/{DB_NAME}"
        )

        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    except Exception as e:
        logger.error(f"Failed to start SSH tunnel: {e}")
        raise HTTPException(status_code=500, detail="SSH Tunnel failed")

# ==================================================
# ✅ SQLALCHEMY ORM DEPENDENCY (MAIN)
# ==================================================
def get_db():
    """
    FastAPI dependency for SQLAlchemy ORM
    """
    start_ssh_tunnel()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================================================
# ✅ PSYCOPG2 RAW CONNECTION
# ==================================================
def get_connection():
    """
    Returns psycopg2 connection (SSH tunnel aware)
    """
    start_ssh_tunnel()
    try:
        return psycopg2.connect(
            host="127.0.0.1",
            port=ssh_tunnel.local_bind_port,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        return None

# ==================================================
# ✅ CURSOR HELPER
# ==================================================
def get_cursor():
    """
    Returns (conn, cursor). Caller must close both.
    Used for local development/Bhavani's routes.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn, conn.cursor()

# ==================================================
# ✅ PSYCOPG2 DEPENDENCY (AUTH / LEGACY MODULES)
# ==================================================
def get_db_psycopg():
    """
    FastAPI dependency for psycopg2-based access
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()

# ==================================================
# ✅ ADMIN / AUTH COMPATIBILITY
# ==================================================
def get_db_conn():
    """
    Compatibility helper for older auth/admin code.
    Returns psycopg2 connection only.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn