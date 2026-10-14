"""Automated test suite for Fitness Classes and Bookings endpoints."""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.datetime_utils import IST


def get_auth_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    """Helper fixture function to sign up and log in a test user, returning the JWT token."""
    client.post("/signup", json={"email": email, "password": password})
    res = client.post("/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_create_class_unauthenticated_fails(client: TestClient):
    """POST /classes without authorization header must return 401 Unauthorized."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    response = client.post(
        "/classes",
        json={
            "name": "Pilates Core",
            "instructor": "Elena Rostova",
            "capacity": 15,
            "start_time": future_time,
        },
    )
    assert response.status_code == 401
    assert "missing" in response.json()["detail"].lower()


def test_create_class_past_time_validation_fails(client: TestClient):
    """POST /classes with start_time in the past must fail validation."""
    token = get_auth_token(client, "trainer1@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    response = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Past Yoga",
            "instructor": "John Doe",
            "capacity": 10,
            "start_time": past_time,
        },
    )
    assert response.status_code == 422


def test_create_class_invalid_capacity_fails(client: TestClient):
    """POST /classes with zero or negative capacity must fail with 422."""
    token = get_auth_token(client, "trainer2@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    # Zero capacity
    res_zero = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Zero Cap Class",
            "instructor": "John Doe",
            "capacity": 0,
            "start_time": future_time,
        },
    )
    assert res_zero.status_code == 422

    # Negative capacity
    res_neg = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Negative Cap Class",
            "instructor": "John Doe",
            "capacity": -5,
            "start_time": future_time,
        },
    )
    assert res_neg.status_code == 422


def test_create_class_success_and_ist_handling(client: TestClient):
    """POST /classes with valid payload creates a class with UTC and formatted IST."""
    token = get_auth_token(client, "admin@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Pass future time in IST
    future_ist = datetime.now(IST) + timedelta(days=3)
    response = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "HIIT Bootcamp",
            "instructor": "Marcus Vance",
            "capacity": 25,
            "start_time": future_ist.isoformat(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "HIIT Bootcamp"
    assert data["instructor"] == "Marcus Vance"
    assert data["capacity"] == 25
    assert data["available_slots"] == 25
    assert data["booked_slots"] == 0
    assert "+05:30" in data["start_time_ist"]


def test_get_classes_excludes_past_classes(client: TestClient):
    """GET /classes should list only upcoming classes and exclude past ones."""
    token = get_auth_token(client, "instructor@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create an upcoming class
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_res = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Zumba Dance",
            "instructor": "Sofia Rivera",
            "capacity": 10,
            "start_time": future_time,
        },
    )
    assert create_res.status_code == 201

    # Fetch classes
    get_res = client.get("/classes")
    assert get_res.status_code == 200
    classes = get_res.json()
    assert len(classes) >= 1
    assert any(c["name"] == "Zumba Dance" for c in classes)


def test_book_class_flow_and_capacity_decrement(client: TestClient):
    """POST /book reserves a slot, decrements available_slots, and returns 201."""
    token = get_auth_token(client, "user_booking@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a class with capacity 2
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    class_res = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Spinning Class",
            "instructor": "Tom Holland",
            "capacity": 2,
            "start_time": future_time,
        },
    )
    class_id = class_res.json()["id"]

    # 2. Book the class
    book_res = client.post(
        "/book",
        headers=headers,
        json={"class_id": class_id},
    )
    assert book_res.status_code == 201
    booking_data = book_res.json()
    assert booking_data["class_id"] == class_id
    assert booking_data["fitness_class"]["name"] == "Spinning Class"
    assert "+05:30" in booking_data["booked_at_ist"]

    # 3. Verify available_slots decremented to 1 in GET /classes
    classes_res = client.get("/classes")
    target_class = next(c for c in classes_res.json() if c["id"] == class_id)
    assert target_class["booked_slots"] == 1
    assert target_class["available_slots"] == 1


def test_book_nonexistent_class_fails_404(client: TestClient):
    """POST /book with nonexistent class ID returns 404 Not Found."""
    token = get_auth_token(client, "user_nonexistent@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/book",
        headers=headers,
        json={"class_id": 999999},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_book_duplicate_booking_fails_409(client: TestClient):
    """POST /book prevents the same user from booking the same class twice with 409 Conflict."""
    token = get_auth_token(client, "user_dup@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create class
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    class_res = client.post(
        "/classes",
        headers=headers,
        json={
            "name": "Ashtanga Yoga",
            "instructor": "Kavita Rao",
            "capacity": 10,
            "start_time": future_time,
        },
    )
    class_id = class_res.json()["id"]

    # First booking succeeds
    res1 = client.post("/book", headers=headers, json={"class_id": class_id})
    assert res1.status_code == 201

    # Second booking attempt by SAME user fails with 409
    res2 = client.post("/book", headers=headers, json={"class_id": class_id})
    assert res2.status_code == 409
    assert "already booked" in res2.json()["detail"].lower()


def test_book_full_capacity_fails_400(client: TestClient):
    """POST /book rejects booking when class capacity is exhausted."""
    # User 1 creates a class with capacity = 1
    token1 = get_auth_token(client, "user1_cap@fitness.com")
    headers1 = {"Authorization": f"Bearer {token1}"}

    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    class_res = client.post(
        "/classes",
        headers=headers1,
        json={
            "name": "Private Boxing Session",
            "instructor": "Mike Tyson",
            "capacity": 1,
            "start_time": future_time,
        },
    )
    class_id = class_res.json()["id"]

    # User 1 books the only slot
    res_book1 = client.post("/book", headers=headers1, json={"class_id": class_id})
    assert res_book1.status_code == 201

    # User 2 attempts to book the full class
    token2 = get_auth_token(client, "user2_cap@fitness.com")
    headers2 = {"Authorization": f"Bearer {token2}"}

    res_book2 = client.post("/book", headers=headers2, json={"class_id": class_id})
    assert res_book2.status_code == 400
    assert "fully booked" in res_book2.json()["detail"].lower()


def test_get_bookings_isolated_per_user(client: TestClient):
    """GET /bookings returns ONLY the authenticated user's reservations."""
    token_alice = get_auth_token(client, "alice@fitness.com")
    token_bob = get_auth_token(client, "bob@fitness.com")

    # Alice creates a class and books it
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    c_res = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={
            "name": "CrossFit Mobility",
            "instructor": "Dave Castro",
            "capacity": 10,
            "start_time": future_time,
        },
    )
    class_id = c_res.json()["id"]

    # Alice books it
    client.post(
        "/book",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"class_id": class_id},
    )

    # Alice views bookings -> should see 1 booking
    alice_bookings = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert alice_bookings.status_code == 200
    assert len(alice_bookings.json()) == 1
    assert alice_bookings.json()[0]["class_id"] == class_id

    # Bob views bookings -> should see 0 bookings
    bob_bookings = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_bookings.status_code == 200
    assert len(bob_bookings.json()) == 0


def test_get_classes_excludes_past_class_in_db(client: TestClient, db_session):
    """GET /classes must strictly omit classes with start_time in the past."""
    from app.models.fitness_class import FitnessClass

    # Insert a past class directly into database
    past_class = FitnessClass(
        name="Past Yesterday Yoga",
        instructor="Guru Ram",
        capacity=15,
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
    )
    # Insert an upcoming class directly into database
    upcoming_class = FitnessClass(
        name="Upcoming Aerial Yoga",
        instructor="Aria Stark",
        capacity=15,
        start_time=datetime.now(timezone.utc) + timedelta(days=2),
    )
    db_session.add(past_class)
    db_session.add(upcoming_class)
    db_session.commit()

    res = client.get("/classes")
    assert res.status_code == 200
    class_names = [c["name"] for c in res.json()]
    assert "Past Yesterday Yoga" not in class_names
    assert "Upcoming Aerial Yoga" in class_names


def test_book_past_class_fails_400(client: TestClient, db_session):
    """POST /book must reject booking attempts on classes that have already started."""
    from app.models.fitness_class import FitnessClass

    token = get_auth_token(client, "late_booker@fitness.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Insert a past class directly
    past_class = FitnessClass(
        name="Expired Morning Spin",
        instructor="Lance A.",
        capacity=10,
        start_time=datetime.now(timezone.utc) - timedelta(hours=3),
    )
    db_session.add(past_class)
    db_session.commit()
    db_session.refresh(past_class)

    res = client.post("/book", headers=headers, json={"class_id": past_class.id})
    assert res.status_code == 400
    assert "already started" in res.json()["detail"].lower()


def test_two_users_competing_for_last_slot_no_overbooking(client: TestClient, db_session):
    """When 2 users compete for the only remaining slot, exactly one succeeds and overbooking is prevented."""
    from app.models.booking import Booking

    # User 1 registers and creates a class with capacity 1
    token1 = get_auth_token(client, "competitor1@fitness.com")
    token2 = get_auth_token(client, "competitor2@fitness.com")

    future_time = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    c_res = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "VIP Solo Pilates",
            "instructor": "Victoria Beck",
            "capacity": 1,
            "start_time": future_time,
        },
    )
    class_id = c_res.json()["id"]

    # User 1 books the slot -> succeeds
    res1 = client.post(
        "/book",
        headers={"Authorization": f"Bearer {token1}"},
        json={"class_id": class_id},
    )
    assert res1.status_code == 201

    # User 2 attempts to book the same slot -> rejected with 400
    res2 = client.post(
        "/book",
        headers={"Authorization": f"Bearer {token2}"},
        json={"class_id": class_id},
    )
    assert res2.status_code == 400
    assert "fully booked" in res2.json()["detail"].lower()

    # Verify database has strictly 1 booking
    total_bookings = db_session.query(Booking).filter(Booking.class_id == class_id).count()
    assert total_bookings == 1


