from dotenv import load_dotenv
import os

load_dotenv()

from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
import logging

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# SSH CONFIG
# --------------------------------------------------
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
   # use key-based auth in prod

# --------------------------------------------------
# DATABASE CONFIG (REMOTE POSTGRES)
# --------------------------------------------------
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
REMOTE_DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
REMOTE_DB_PORT = int(os.getenv("DB_PORT", 5432))

ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)

# --------------------------------------------------
# AWS S3 CONFIG (NO .env)
# --------------------------------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_POLICY_FOLDER = os.getenv("AWS_S3_POLICY_FOLDER")

# --------------------------------------------------
# START SSH TUNNEL (ONCE)
# --------------------------------------------------
logger.info("Starting SSH tunnel to database...")

ssh_tunnel = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(REMOTE_DB_HOST, REMOTE_DB_PORT),
)

ssh_tunnel.start()

logger.info(
    f"SSH tunnel established on localhost:{ssh_tunnel.local_bind_port}"
)

# --------------------------------------------------
# SQLALCHEMY DATABASE URL
# --------------------------------------------------
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{ENCODED_DB_PASSWORD}"
    f"@127.0.0.1:{ssh_tunnel.local_bind_port}/{DB_NAME}"
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
# FASTAPI DEPENDENCY (ORM)
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
    Returns raw psycopg connection
    (use for existing cursor-based queries)
    """
    return engine.raw_connection()
