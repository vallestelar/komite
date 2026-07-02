import hashlib

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _normalize_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password

    digest = hashlib.sha256(password_bytes).hexdigest()
    return f"sha256:{digest}"


def hash_password(password: str) -> str:
    return pwd_context.hash(_normalize_password(password))


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(_normalize_password(plain_password), hashed_password)

