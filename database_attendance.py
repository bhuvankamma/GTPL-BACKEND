import pg8000
from sshtunnel import SSHTunnelForwarder
from utils.config_attendance import (
    SSH_HOST,
    SSH_PORT,
    SSH_USER,
    SSH_PASSWORD,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)

_ssh_tunnel = None


def get_db():
    global _ssh_tunnel

    if _ssh_tunnel is None or not _ssh_tunnel.is_active:
        _ssh_tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=("127.0.0.1", 5432)
        )
        _ssh_tunnel.start()

    return pg8000.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host="127.0.0.1",
        port=_ssh_tunnel.local_bind_port,
        database=DB_NAME
    )
