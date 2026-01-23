import logging
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

SSH_HOST = "122.186.222.20"
SSH_PORT = 22
SSH_USER = "hrmsadmin"
SSH_PASSWORD = "Dell@123"

DB_HOST = "127.0.0.1"
DB_PORT = 5432
DB_USER = "hrms_user"
DB_PASSWORD = quote_plus("Loveudad43#")
DB_NAME = "hrms_crm"

ssh_tunnel = None
engine = None
SessionLocal = None


def start_ssh_tunnel():
    global ssh_tunnel, engine, SessionLocal

    if ssh_tunnel and ssh_tunnel.is_active:
        return

    logger.info("Starting SSH tunnel...")

    ssh_tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST, DB_PORT)
    )

    ssh_tunnel.start()

    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
        f"@127.0.0.1:{ssh_tunnel.local_bind_port}/{DB_NAME}"
    )

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )


def get_db():
    start_ssh_tunnel()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
