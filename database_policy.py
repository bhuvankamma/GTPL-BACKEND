from dotenv import load_dotenv
import os
import logging
from urllib.parse import quote_plus

from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --------------------------------------------------
# LOAD ENV
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database_policy")

# --------------------------------------------------
# FEATURE FLAG (CRITICAL)
# --------------------------------------------------
USE_POLICY_SSH = os.getenv("USE_POLICY_SSH", "false").lower() == "true"

# --------------------------------------------------
# SSH CONFIG
# --------------------------------------------------
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # key-based auth recommended in prod

# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

REMOTE_DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
REMOTE_DB_PORT = int(os.getenv("DB_PORT", 5432))

ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)

# --------------------------------------------------
# AWS S3 CONFIG (OPTIONAL, SAFE)
# --------------------------------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_POLICY_FOLDER = os.getenv("AWS_S3_POLICY_FOLDER")

# --------------------------------------------------
# SSH TUNNEL (OPTIONAL, SAFE)
# --------------------------------------------------
LOCAL_DB_PORT = REMOTE_DB_PORT
ssh_tunnel = None

if USE_POLICY_SSH:
    logger.info("USE_POLICY_SSH=true → starting SSH tunnel")

    if not SSH_HOST:
        raise RuntimeError("SSH_HOST must be set when USE_POLICY_SSH=true")

    ssh_tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(REMOTE_DB_HOST, REMOTE_DB_PORT),
    )

    ssh_tunnel.start()
    LOCAL_DB_PORT = ssh_tunnel.local_bind_port

    logger.info(f"SSH tunnel established on localhost:{LOCAL_DB_PORT}")
else:
    logger.info("USE_POLICY_SSH=false → running without SSH tunnel")

# --------------------------------------------------
# DATABASE URL
# --------------------------------------------------
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{ENCODED_DB_PASSWORD}"
    f"@127.0.0.1:{LOCAL_DB_PORT}/{DB_NAME}"
)

# --------------------------------------------------
# SQLALCHEMY ENGINE
# --------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# --------------------------------------------------
# SESSION
# --------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# --------------------------------------------------
# FASTAPI ORM DEPENDENCY
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------
# RAW CONNECTION (CURSOR-BASED)
# --------------------------------------------------
def get_db_conn():
    """
    Returns raw psycopg2 connection
    (use for legacy cursor-based queries)
    """
    return engine.raw_connection()
