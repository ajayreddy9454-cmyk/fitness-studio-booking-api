"""Pydantic schema definitions."""

from app.schemas.user import UserBase, UserCreate, UserLogin, UserResponse
from app.schemas.token import Token, TokenData
from app.schemas.fitness_class import (
    FitnessClassBase,
    FitnessClassCreate,
    FitnessClassResponse,
)
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    ClassSummary,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "FitnessClassBase",
    "FitnessClassCreate",
    "FitnessClassResponse",
    "BookingCreate",
    "BookingResponse",
    "ClassSummary",
]
