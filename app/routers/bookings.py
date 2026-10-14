"""Router for fitness class booking management (reservations and viewing user bookings)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.datetime_utils import get_current_utc, format_iso_ist, to_utc_aware, to_ist
from app.models.user import User

from app.models.fitness_class import FitnessClass
from app.models.booking import Booking
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    ClassSummary,
)

router = APIRouter(tags=["Bookings"])


@router.post(
    "/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a fitness class",
    description=(
        "Reserves a slot in a scheduled fitness class for the authenticated user. "
        "Requires a valid JWT Bearer token. "
        "Validates that the class exists, has not already started, is not fully booked, "
        "and that the user has not already booked this class."
    ),
)
def book_class(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    """Book a fitness class for the currently authenticated user.

    Args:
        booking_in: Payload containing class_id to reserve.
        current_user: Authenticated user making the reservation.
        db: Scoped database session.

    Returns:
        Created booking details with embedded class summary.

    Raises:
        HTTPException: 404 Not Found if the class ID does not exist.
        HTTPException: 400 Bad Request if the class has already started or is fully booked.
        HTTPException: 409 Conflict if the user already has a reservation for this class.
    """
    # 1. Fetch class from database
    fitness_class = (
        db.query(FitnessClass)
        .filter(FitnessClass.id == booking_in.class_id)
        .first()
    )
    if not fitness_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fitness class with ID {booking_in.class_id} was not found.",
        )

    # 2. Reject classes that have already started
    now_utc = get_current_utc()
    class_start_utc = to_utc_aware(fitness_class.start_time)
    if class_start_utc <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a class that has already started or completed.",
        )

    # 3. Check if user already booked this class (pre-insert check)
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.user_id == current_user.id,
            Booking.class_id == fitness_class.id,
        )
        .first()
    )
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked a slot in this class.",
        )

    # 4. Check available capacity (prevent overbooking)
    booked_count: int = (
        db.query(func.count(Booking.id))
        .filter(Booking.class_id == fitness_class.id)
        .scalar()
        or 0
    )
    if booked_count >= fitness_class.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is fully booked. No remaining slots available.",
        )

    # 5. Insert new booking within database transaction
    new_booking = Booking(
        user_id=current_user.id,
        class_id=fitness_class.id,
    )
    db.add(new_booking)

    try:
        db.commit()
        db.refresh(new_booking)
    except IntegrityError:
        db.rollback()
        # Database UniqueConstraint('user_id', 'class_id') catches concurrent duplicate requests
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked a slot in this class.",
        )

    return BookingResponse(
        id=new_booking.id,
        user_id=new_booking.user_id,
        class_id=new_booking.class_id,
        booked_at=to_ist(new_booking.booked_at),
        booked_at_ist=format_iso_ist(new_booking.booked_at),
        fitness_class=ClassSummary(
            id=fitness_class.id,
            name=fitness_class.name,
            instructor=fitness_class.instructor,
            start_time=to_ist(fitness_class.start_time),
            start_time_ist=format_iso_ist(fitness_class.start_time),
            capacity=fitness_class.capacity,
        ),
    )




@router.get(
    "/bookings",
    response_model=List[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="List current user's bookings",
    description=(
        "Retrieves all fitness class bookings belonging ONLY to the currently authenticated user. "
        "Includes class details and booking timestamps formatted in both UTC and IST."
    ),
)
def get_user_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BookingResponse]:
    """Retrieve all bookings belonging to the authenticated user.

    Args:
        current_user: Authenticated user.
        db: Scoped database session.

    Returns:
        List of user's bookings with class details.
    """
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.booked_at.desc())
        .all()
    )

    results: List[BookingResponse] = []
    for b in bookings:
        fc = b.fitness_class
        results.append(
            BookingResponse(
                id=b.id,
                user_id=b.user_id,
                class_id=b.class_id,
                booked_at=to_ist(b.booked_at),
                booked_at_ist=format_iso_ist(b.booked_at),
                fitness_class=ClassSummary(
                    id=fc.id,
                    name=fc.name,
                    instructor=fc.instructor,
                    start_time=to_ist(fc.start_time),
                    start_time_ist=format_iso_ist(fc.start_time),
                    capacity=fc.capacity,
                ),
            )
        )

    return results

