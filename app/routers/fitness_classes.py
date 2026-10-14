"""Router for fitness class management (creation and upcoming class listing)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.datetime_utils import get_current_utc, format_iso_ist, to_utc_aware, to_ist, get_current_ist
from app.models.user import User

from app.models.fitness_class import FitnessClass
from app.models.booking import Booking
from app.schemas.fitness_class import (
    FitnessClassCreate,
    FitnessClassResponse,
)

router = APIRouter(tags=["Fitness Classes"])


@router.post(
    "/classes",
    response_model=FitnessClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fitness class",
    description=(
        "Creates a new fitness class with a name, instructor, start time, and capacity. "
        "Requires a valid JWT Bearer authentication token. "
        "Validates that capacity is a positive integer (> 0) and that the start time is in the future."
    ),
)
def create_class(
    class_in: FitnessClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FitnessClassResponse:
    """Create a new fitness class session.

    Args:
        class_in: Validated class creation data.
        current_user: Authenticated user creating the class.
        db: Scoped database session.

    Returns:
        The created fitness class details, including formatted IST start time and available slots.
    """
    new_class = FitnessClass(
        name=class_in.name.strip(),
        instructor=class_in.instructor.strip(),
        capacity=class_in.capacity,
        start_time=class_in.start_time,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return FitnessClassResponse(
        id=new_class.id,
        name=new_class.name,
        instructor=new_class.instructor,
        capacity=new_class.capacity,
        start_time=to_ist(new_class.start_time),
        start_time_ist=format_iso_ist(new_class.start_time),
        booked_slots=0,
        available_slots=new_class.capacity,
        created_at=to_ist(new_class.created_at) if new_class.created_at else get_current_ist(),
    )



@router.get(
    "/classes",
    response_model=List[FitnessClassResponse],
    status_code=status.HTTP_200_OK,
    summary="List upcoming fitness classes",
    description=(
        "Lists upcoming scheduled fitness classes. "
        "Strictly excludes classes whose start time is in the past. "
        "Each class returns real-time slot availability (total capacity minus reserved bookings) "
        "and start times in both standard UTC and formatted IST (UTC+05:30)."
    ),
)
def list_classes(
    db: Session = Depends(get_db),
) -> List[FitnessClassResponse]:
    """Retrieve all upcoming scheduled fitness classes.

    Args:
        db: Scoped database session.

    Returns:
        List of upcoming fitness classes with available slot counts.
    """
    now_utc = get_current_utc()

    # Query upcoming classes starting after current time, ordered by start time
    upcoming_classes = (
        db.query(FitnessClass)
        .filter(FitnessClass.start_time > now_utc)
        .order_by(FitnessClass.start_time.asc())
        .all()
    )

    results: List[FitnessClassResponse] = []
    for fc in upcoming_classes:
        # Count currently active reservations for this class
        booked_count: int = (
            db.query(func.count(Booking.id))
            .filter(Booking.class_id == fc.id)
            .scalar()
            or 0
        )
        available = max(0, fc.capacity - booked_count)

        results.append(
            FitnessClassResponse(
                id=fc.id,
                name=fc.name,
                instructor=fc.instructor,
                capacity=fc.capacity,
                start_time=to_ist(fc.start_time),
                start_time_ist=format_iso_ist(fc.start_time),
                booked_slots=booked_count,
                available_slots=available,
                created_at=to_ist(fc.created_at) if fc.created_at else get_current_ist(),
            )
        )


    return results
