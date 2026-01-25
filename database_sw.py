import logging
import threading
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import boto3
import os

# --------------------------------------------------
# LOAD ENV (ONLY AWS)
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# SSH CONFIG (HARDCODED)
# --------------------------------------------------
USE_SSH = True  

SSH_HOST = os.getenv("SSH_HOST", "122.186.222.20")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER", "hrmsadmin")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "Dell@123")

# --------------------------------------------------
# DATABASE CONFIG (HARDCODED)
# --------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "hrms_user")
DB_PASSWORD = os.getenv("DB_PASSWORD","Loveudad43#")
DB_NAME = os.getenv("DB_NAME", "hrms_crm")

ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)

# --------------------------------------------------
# AWS CONFIG (FROM .env ONLY)
# --------------------------------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_REIMBURSEMENT_FOLDER = os.getenv("AWS_S3_REIMBURSEMENT_FOLDER")

# --------------------------------------------------
# AWS S3 CLIENT
# --------------------------------------------------
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# --------------------------------------------------
# GLOBALS
# --------------------------------------------------
ssh_tunnel = None
engine = None
SessionLocal = None
lock = threading.Lock()

Base = declarative_base()

# --------------------------------------------------
# INIT DB (LAZY)
# --------------------------------------------------
def init_db():
    global ssh_tunnel, engine, SessionLocal

    with lock:
        if engine:
            return

        logger.info("Initializing database...")

        local_port = DB_PORT

        if USE_SSH:
            logger.info("Starting SSH tunnel...")
            ssh_tunnel = SSHTunnelForwarder(
                (SSH_HOST, SSH_PORT),
                ssh_username=SSH_USER,
                ssh_password=SSH_PASSWORD,
                remote_bind_address=(DB_HOST, DB_PORT),
            )
            ssh_tunnel.start()
            local_port = ssh_tunnel.local_bind_port
            logger.info(f"SSH tunnel started on port {local_port}")

        DATABASE_URL = (
            f"postgresql+psycopg://{DB_USER}:{ENCODED_DB_PASSWORD}"
            f"@127.0.0.1:{local_port}/{DB_NAME}"
        )

        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )

        logger.info("Database initialized successfully")

# --------------------------------------------------
# FASTAPI DEPENDENCY
# --------------------------------------------------
def get_db():
    if engine is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------
# SHUTDOWN
# --------------------------------------------------
def close_db():
    global ssh_tunnel, engine

    if engine:
        engine.dispose()
        logger.info("DB engine disposed")

    if ssh_tunnel:
        ssh_tunnel.stop()
        logger.info("SSH tunnel closed")
