"""Security utilities for password hashing and JWT token operations.

Uses bcrypt directly for industry-standard salted password hashing
and PyJWT for creating and validating cryptographically signed tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with a randomly generated salt.

    Args:
        password: The plaintext password string to hash.

    Returns:
        The resulting bcrypt hashed string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The plaintext password provided by the user.
        hashed_password: The bcrypt hash retrieved from the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates and cryptographically signs a JWT access token.

    Args:
        subject: The primary identifier of the subject (e.g. user email or ID).
        expires_delta: Optional custom lifetime duration for the token.

    Returns:
        A signed JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decodes and validates a signed JWT access token.

    Args:
        token: The signed JWT token string.

    Returns:
        The decoded payload dictionary if valid, or None if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
