import os
import logging
import pg8000
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
# Try to import Likith's config, but fallback to local vars if not found
try:
    from models.config import SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
except ImportError:
    SSH_HOST = os.getenv("SSH_HOST", "122.186.222.20")
    SSH_PORT = int(os.getenv("SSH_PORT", 22))
    SSH_USER = os.getenv("SSH_USER", "hrmsadmin")
    SSH_PASSWORD = os.getenv("SSH_PASSWORD", "Dell@123")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "hrms_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Loveudad43#")
    DB_NAME = os.getenv("DB_NAME", "hrms_crm")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# CONFIGURATION TOGGLE
# --------------------------------------------------
USE_SSH = os.getenv("USE_SSH", "false").lower() == "true"

ssh_tunnel = None
final_host = DB_HOST
final_port = DB_PORT

# --------------------------------------------------
# CONDITIONAL SSH TUNNEL START
# --------------------------------------------------
if USE_SSH:
    try:
        if ssh_tunnel is None or not ssh_tunnel.is_active:
            logger.info("Starting SSH tunnel...")
            ssh_tunnel = SSHTunnelForwarder(
                (SSH_HOST, SSH_PORT),
                ssh_username=SSH_USER,
                ssh_password=SSH_PASSWORD,
                remote_bind_address=(DB_HOST, DB_PORT),
                allow_agent=False
            )
            ssh_tunnel.start()
        final_host = "127.0.0.1"
        final_port = ssh_tunnel.local_bind_port
        logger.info(f"SSH tunnel established on localhost:{final_port}")
    except Exception as e:
        logger.error(f"Failed to start SSH tunnel: {e}")
else:
    logger.info("SSH Tunneling is DISABLED. Connecting directly to database.")

# --------------------------------------------------
# SQLALCHEMY ENGINE (Used by Core, Sravya, Bhavani)
# --------------------------------------------------
ENCODED_DB_PASSWORD = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{ENCODED_DB_PASSWORD}@{final_host}:{final_port}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --------------------------------------------------
# LIKITH'S CONNECTION FUNCTION (pg8000)
# --------------------------------------------------
def get_db():
    """
    Likith's specific connection method using pg8000
    """
    global ssh_tunnel
    
    # Ensure tunnel is up if USE_SSH is true
    current_port = final_port
    if USE_SSH and (ssh_tunnel is None or not ssh_tunnel.is_active):
        ssh_tunnel.start()
        current_port = ssh_tunnel.local_bind_port

    conn = pg8000.connect(
        host=final_host,
        port=current_port,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def get_connection():
    """ Returns raw psycopg connection for cursor usage """
    return engine.raw_connection().connection