from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sshtunnel import SSHTunnelForwarder

from models.config import (
    SSH_HOST,
    SSH_PORT,
    SSH_USER,
    SSH_PASSWORD,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
)

ssh_tunnel = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=("127.0.0.1", DB_PORT)
)
ssh_tunnel.start()

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@127.0.0.1:{ssh_tunnel.local_bind_port}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
