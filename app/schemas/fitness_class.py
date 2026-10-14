"""Pydantic schemas for FitnessClass validation, serialization, and date-time handling."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.datetime_utils import ensure_utc, get_current_utc


class FitnessClassBase(BaseModel):
    """Shared fields for fitness class operations."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the fitness class",
        examples=["Morning Vinyasa Yoga"],
    )
    instructor: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the instructor",
        examples=["Maya Sharma"],
    )
    capacity: int = Field(
        ...,
        gt=0,
        description="Available capacity for attendees (must be a positive integer)",
        examples=[20],
    )
    start_time: datetime = Field(
        ...,
        description=(
            "Scheduled class start time in ISO 8601 format. "
            "If timezone offset is omitted, IST (UTC+05:30) is assumed. "
            "Must be set to a future date and time."
        ),
        examples=["2026-10-15T09:00:00+05:30"],
    )

    @field_validator("start_time")
    @classmethod
    def validate_future_start_time(cls, v: datetime) -> datetime:
        """Normalizes start_time to UTC and validates that it is strictly in the future."""
        utc_time = ensure_utc(v)
        if utc_time <= get_current_utc():
            raise ValueError("Class start time must be in the future.")
        return utc_time


class FitnessClassCreate(FitnessClassBase):
    """Schema for validating POST /classes requests."""
    pass


class FitnessClassResponse(BaseModel):
    """Schema for returning fitness class details to clients."""

    id: int
    name: str
    instructor: str
    capacity: int
    start_time: datetime
    start_time_ist: str = Field(
        ...,
        description="Class start time formatted in Indian Standard Time (IST, UTC+05:30)",
    )
    booked_slots: int = Field(..., description="Number of currently reserved slots")
    available_slots: int = Field(..., description="Remaining slots available for booking")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
