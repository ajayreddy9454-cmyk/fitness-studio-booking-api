"""Pydantic schemas for Booking creation and response serialization."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    """Schema for validating POST /book reservation requests."""

    class_id: int = Field(
        ...,
        gt=0,
        description="The ID of the fitness class session to reserve",
        examples=[1],
    )


class ClassSummary(BaseModel):
    """Summarized fitness class details embedded in booking responses."""

    id: int
    name: str
    instructor: str
    start_time: datetime
    start_time_ist: str
    capacity: int

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    """Schema for returning booking reservations to clients."""

    id: int
    user_id: int
    class_id: int
    booked_at: datetime
    booked_at_ist: str = Field(
        ...,
        description="Booking timestamp formatted in Indian Standard Time (IST, UTC+05:30)",
    )
    fitness_class: ClassSummary

    model_config = ConfigDict(from_attributes=True)
