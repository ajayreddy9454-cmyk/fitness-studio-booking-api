"""Pydantic schemas for authentication tokens."""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema for JWT token response returned on successful login."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")


class TokenData(BaseModel):
    """Schema for data extracted from a validated JWT access token."""

    email: str | None = None
