"""Pydantic schemas for User validation and serialization."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Shared properties for user schemas."""

    email: EmailStr = Field(
        ...,
        description="Valid email address used for account identification",
        examples=["member@fitnessstudio.com"],
    )


class UserCreate(UserBase):
    """Schema for validating user registration requests."""

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Account password (minimum 6 characters)",
        examples=["StrongP@ssw0rd!"],
    )


class UserLogin(UserBase):
    """Schema for validating user login requests."""

    password: str = Field(
        ...,
        min_length=1,
        description="Account password",
        examples=["StrongP@ssw0rd!"],
    )


class UserResponse(UserBase):
    """Schema for returning user data in API responses (never exposes password hash)."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
