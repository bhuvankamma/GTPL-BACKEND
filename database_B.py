from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
import logging
import os
import boto3
import pg8000
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# TOGGLE & CONFIG
# --------------------------------------------------
USE_SSH = os.getenv("USE_SSH", "false").lower() == "true"

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# --------------------------------------------------
# AWS S3 CLIENT
# --------------------------------------------------
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# SSH/DB Config
SSH_HOST = os.getenv("SSH_HOST", "122.186.222.20")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER", "hrmsadmin")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "Dell@123")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "hrms_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Loveudad43#")
DB_NAME = os.getenv("DB_NAME", "hrms_crm")
ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)

ssh_tunnel = None
final_host = DB_HOST
final_port = DB_PORT

# --------------------------------------------------
# START SSH TUNNEL (CONDITIONAL)
# --------------------------------------------------
if USE_SSH:
    try:
        logger.info("database_b: Starting SSH tunnel...")
        ssh_tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST, DB_PORT),
        )
        ssh_tunnel.start()
        final_host = "127.0.0.1"
        final_port = ssh_tunnel.local_bind_port
        logger.info(f"✅ SSH tunnel established on localhost:{final_port}")
    except Exception as e:
        logger.error(f"❌ database_b: Failed to start SSH tunnel: {e}")
else:
    logger.info("database_b: SSH Tunneling is DISABLED. Connecting directly.")

# --------------------------------------------------
# SQLALCHEMY ENGINE
# --------------------------------------------------
DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{ENCODED_DB_PASSWORD}"
    f"@{final_host}:{final_port}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# --------------------------------------------------
# RAW CONNECTION (FOR CURSOR USAGE)
# --------------------------------------------------
def get_connection():
    return engine.raw_connection()

def get_db_conn():
    """
    Used by pg8000 for specific Bhavani routes.
    """
    return pg8000.connect(
        host=final_host,
        port=final_port,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl_context=None,
        timeout=30
    )