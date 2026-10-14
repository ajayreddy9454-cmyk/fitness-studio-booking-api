"""Authentication router for user registration (signup) and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Registers a new user account with an email and password. "
        "Rejects duplicate email addresses with HTTP 409 Conflict. "
        "The password is securely hashed with bcrypt before saving."
    ),
)
def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Register a new user account.

    Args:
        user_in: Validated signup payload containing email and password.
        db: Database session dependency.

    Returns:
        The newly created user profile (excluding password).

    Raises:
        HTTPException: 409 Conflict if the email is already in use.
    """
    # Normalize email to lower case for consistent matching
    normalized_email = user_in.email.strip().lower()

    # Check if a user with this email already exists
    existing_user = (
        db.query(User).filter(User.email == normalized_email).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Securely hash the plaintext password using bcrypt
    hashed_pwd = hash_password(user_in.password)

    # Create new User database instance
    new_user = User(
        email=normalized_email,
        hashed_password=hashed_pwd,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description=(
        "Authenticates a user with email and password. "
        "Returns a signed JWT access token upon successful credentials verification."
    ),
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user credentials and issue an access token.

    Args:
        credentials: Login payload containing email and plaintext password.
        db: Database session dependency.

    Returns:
        JWT access token and token type ('bearer').

    Raises:
        HTTPException: 401 Unauthorized if email not found or password incorrect.
    """
    # Normalize email to lower case
    normalized_email = credentials.email.strip().lower()

    # Retrieve user record by email
    user = db.query(User).filter(User.email == normalized_email).first()

    # Verify user exists and the provided password matches the stored bcrypt hash
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue a signed JWT access token containing the user's email as subject ('sub')
    access_token = create_access_token(subject=user.email)

    return Token(
        access_token=access_token,
        token_type="bearer",
    )
