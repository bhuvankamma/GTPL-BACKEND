import pg8000
from sshtunnel import SSHTunnelForwarder
from models.config import *

_tunnel = None

def get_db():
    global _tunnel

    # Start SSH tunnel once
    if _tunnel is None or not _tunnel.is_active:
        _tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            allow_agent=False,  # ✅ supported
            remote_bind_address=("127.0.0.1", DB_PORT),
        )
        _tunnel.start()

    # Create new DB connection per request
    conn = pg8000.connect(
        host="127.0.0.1",
        port=_tunnel.local_bind_port,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    return conn
