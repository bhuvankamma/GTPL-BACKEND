from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _normalize_password(password: str) -> str:
    """
    bcrypt supports max 72 bytes.
    Truncate safely to avoid runtime errors.
    """
    if not password:
        return password
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def hash_password(password: str) -> str:
    password = _normalize_password(password)
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    password = _normalize_password(password)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):

    return pwd_context.verify(password, hashed)
