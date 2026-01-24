from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# CONFIGURATION TOGGLE
# --------------------------------------------------
# Set USE_SSH=true in your .env if you need the tunnel. Default is false.
USE_SSH = os.getenv("USE_SSH", "false").lower() == "true"

# --------------------------------------------------
# SSH & DATABASE CONFIG
# --------------------------------------------------
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
# CONDITIONAL SSH TUNNEL START
# --------------------------------------------------
if USE_SSH:
    try:
        logger.info("Starting SSH tunnel...")
        ssh_tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST, DB_PORT),
        )
        ssh_tunnel.start()
        final_host = "127.0.0.1"
        final_port = ssh_tunnel.local_bind_port
        logger.info(f"SSH tunnel established on localhost:{final_port}")
    except Exception as e:
        logger.error(f"Failed to start SSH tunnel: {e}")
        # If tunnel fails, we try to fall back to direct connection
else:
    logger.info("SSH Tunneling is DISABLED. Connecting directly to database.")

# --------------------------------------------------
# SQLALCHEMY ENGINE
# --------------------------------------------------
# Using psycopg2 (standard) or psycopg (v3) - adjusted based on your URL
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
    """
    Returns a raw psycopg connection
    Useful for cursor-based SQL (legacy / lambda-style code)
    """
    return engine.raw_connection().connection