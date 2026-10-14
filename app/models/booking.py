"""Booking database model definition."""

from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Booking(Base):
    """Booking ORM model representing a user's reservation for a fitness class.

    Enforces business rules:
    - UniqueConstraint('user_id', 'class_id') ensures at the database level
      that a user cannot book the same class session more than once.
    - Foreign keys cascade on delete to maintain relational integrity.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "class_id", name="uq_user_class_booking"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fitness_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="bookings")
    fitness_class = relationship("FitnessClass", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} class_id={self.class_id}>"
