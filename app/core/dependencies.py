"""FastAPI dependencies for authentication, user verification, and database sessions."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# HTTPBearer security scheme automatically adds the Authorize button in /docs
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that authenticates incoming requests using a Bearer JWT token.

    Validates:
    1. That the Authorization header with Bearer token is provided.
    2. That the JWT token signature is valid and not expired.
    3. That the user referenced in the token subject ('sub') exists in the database.

    Args:
        auth_header: The HTTP Authorization Bearer credentials extracted by FastAPI.
        db: Scoped database session.

    Returns:
        The authenticated User model instance.

    Raises:
        HTTPException: 401 Unauthorized if the token is missing, invalid, expired,
                       or the user no longer exists.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.credentials.strip()
    # Strip optional duplicate 'Bearer ' prefix if entered in Swagger UI Authorize dialog
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    payload = decode_access_token(token)


    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_email: str = payload["sub"]
    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user account associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
