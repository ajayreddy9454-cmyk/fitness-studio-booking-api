"""Fitness class database model definition."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FitnessClass(Base):
    """FitnessClass ORM model representing scheduled studio workout sessions.

    Attributes:
        id: Primary key unique integer identifier.
        name: Title of the class (e.g., 'Morning Vinyasa Yoga').
        instructor: Name of the fitness instructor conducting the session.
        start_time: Timezone-aware UTC scheduled start time.
        capacity: Maximum number of attendees allowed. Must be a positive integer.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        bookings: Relationship list of all bookings made for this class session.
    """

    __tablename__ = "fitness_classes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    instructor: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    bookings = relationship(
        "Booking",
        back_populates="fitness_class",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FitnessClass id={self.id} name='{self.name}' instructor='{self.instructor}'>"
