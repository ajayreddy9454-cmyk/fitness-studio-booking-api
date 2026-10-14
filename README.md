# Fitness Studio Booking API

A backend RESTful API built for managing fitness studio class schedules and member bookings. This project was developed as part of the Python Backend Developer Intern assignment for Starlabs Technologies.

---

## Project Overview

Fitness studios frequently struggle with manual scheduling, accidental double-bookings, and managing capacity limits for popular sessions. This project provides a structured backend service to handle:

- User account registration and secure JWT authentication.
- Fitness class scheduling with capacity management and start time validation.
- Real-time slot availability for upcoming classes.
- Atomic slot bookings that prevent overbooking and duplicate reservations.
- Timezone-safe date handling, storing all schedules in UTC while supporting Indian Standard Time (IST, UTC+05:30).

---

## Tech Stack

- **Language:** Python 3.12 (compatible with Python 3.10+)
- **Framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy 2.0
- **Data Validation & Settings:** Pydantic v2 & Pydantic-Settings
- **Security & Authentication:** PyJWT and bcrypt
- **Server:** Uvicorn
- **Automated Testing:** Pytest and HTTPX (FastAPI TestClient)

---

## Database Design

The database uses SQLite with three relational tables defined via SQLAlchemy ORM models:

### 1. `users`
Stores registered member accounts.
- `id` (Integer, Primary Key, Indexed)
- `email` (String(255), Unique, Indexed, Not Null)
- `hashed_password` (String(255), Not Null) – Salted hash generated using bcrypt
- `created_at` (DateTime, UTC, Default: current time)
- `updated_at` (DateTime, UTC, Default: current time, Auto-updated)

### 2. `fitness_classes`
Stores scheduled workout sessions.
- `id` (Integer, Primary Key, Indexed)
- `name` (String(100), Indexed, Not Null) – e.g., "Morning Vinyasa Yoga"
- `instructor` (String(100), Not Null) – e.g., "Aarav Sharma"
- `start_time` (DateTime, UTC, Indexed, Not Null) – Scheduled start time
- `capacity` (Integer, Not Null) – Maximum number of attendees allowed (> 0)
- `created_at` (DateTime, UTC, Default: current time)
- `updated_at` (DateTime, UTC, Default: current time, Auto-updated)

### 3. `bookings`
Represents an individual user's reservation for a class.
- `id` (Integer, Primary Key, Indexed)
- `user_id` (Integer, Foreign Key to `users.id`, On Delete CASCADE, Indexed)
- `class_id` (Integer, Foreign Key to `fitness_classes.id`, On Delete CASCADE, Indexed)
- `booked_at` (DateTime, UTC, Default: current time)
- **Constraint:** `UniqueConstraint('user_id', 'class_id', name='uq_user_class_booking')` ensures at the database level that a member cannot book the same class twice.

---

## Core Features & Booking Validation

### Authentication Flow
- Passwords are encrypted with `bcrypt` using an auto-generated per-user salt. Plaintext passwords are never saved or returned in responses.
- Logging in verifies the credentials and returns a cryptographically signed JWT token signed with HMAC-SHA256 (`HS256`).
- Protected endpoints use FastAPI's `HTTPBearer` security dependency to extract and validate the JWT token.

### Timezone Handling
- All timestamps are normalized and persisted in UTC in the database.
- Input datetimes without a timezone offset are interpreted as Indian Standard Time (IST, UTC+05:30), which matches the studio's operational context.
- Responses return both standard ISO datetime format and formatted IST strings (`start_time_ist`, `booked_at_ist`) for direct frontend display.

### Booking Validation Logic
When a booking request (`POST /book`) is received, the API validates:
1. **Class existence:** Returns `404 Not Found` if the provided `class_id` does not exist.
2. **Class schedule:** Returns `400 Bad Request` if the class has already started or is in the past.
3. **Duplicate reservation:** Returns `409 Conflict` if the current user has already booked this class.
4. **Capacity check:** Checks `booked_slots` against `capacity`. If `booked_slots >= capacity`, returns `400 Bad Request` ("Class is fully booked").
5. **Database concurrency safety:** The database-level `UniqueConstraint('user_id', 'class_id')` ensures concurrent duplicate requests are caught even if two requests pass initial application checks simultaneously.

---

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Redirects to Swagger UI documentation (`/docs`) |
| `GET` | `/health` | No | Returns API status, version, and server timestamp |
| `POST` | `/signup` | No | Register a new user account |
| `POST` | `/login` | No | Authenticate user and receive JWT Bearer token |
| `POST` | `/classes` | Yes (Bearer) | Create a new scheduled fitness class |
| `GET` | `/classes` | No | List upcoming classes with available slot counts |
| `POST` | `/book` | Yes (Bearer) | Book a slot in an upcoming class |
| `GET` | `/bookings` | Yes (Bearer) | List all class bookings for the authenticated user |

---

## Project Structure

```text
fitness-studio-api/
├── app/
│   ├── __init__.py              # Package initializer
│   ├── main.py                  # FastAPI app setup, lifespan, and router mounting
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Environment settings with Pydantic BaseSettings
│   │   ├── database.py          # SQLAlchemy engine, session maker, get_db dependency
│   │   ├── datetime_utils.py    # UTC and IST timezone conversion helpers
│   │   ├── dependencies.py      # get_current_user JWT authentication dependency
│   │   └── security.py          # bcrypt password hashing and PyJWT token generation
│   ├── models/
│   │   ├── __init__.py          # Model exports (User, FitnessClass, Booking)
│   │   ├── user.py              # User ORM model
│   │   ├── fitness_class.py     # FitnessClass ORM model
│   │   └── booking.py           # Booking ORM model with UniqueConstraint
│   ├── schemas/
│   │   ├── __init__.py          # Schema exports
│   │   ├── token.py             # JWT token response schemas
│   │   ├── user.py              # User signup, login, and response schemas
│   │   ├── fitness_class.py     # Class creation and response schemas with slot counts
│   │   └── booking.py           # Booking request and response schemas
│   └── routers/
│       ├── __init__.py
│       ├── auth.py              # /signup and /login routes
│       ├── health.py            # /health route
│       ├── fitness_classes.py   # /classes routes (create and list upcoming)
│       └── bookings.py          # /book and /bookings routes
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and in-memory SQLite setup
│   ├── test_auth.py             # Unit tests for authentication and token validation
│   └── test_classes_and_bookings.py # Unit tests for classes, bookings, and concurrency
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusion rules
├── requirements.txt             # Pinned project dependencies
└── README.md                    # Project documentation
```

---

## Setup and Installation (Windows PowerShell)

### 1. Prerequisites
- Python 3.10 or higher installed. Verify with:
  ```powershell
  python --version
  ```
- Git installed on your system.

### 2. Clone the Repository
```powershell
git clone <repository-url>
cd <project-folder>
```

### 3. Create and Activate a Virtual Environment
```powershell
# Create the virtual environment
python -m venv .venv

# Activate it in PowerShell
.venv\Scripts\Activate.ps1
```
> *Note:* If PowerShell blocks script execution, open PowerShell and run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to create your local `.env` file:
```powershell
Copy-Item .env.example .env
```

The application defaults work out of the box for local development:
```env
PROJECT_NAME="Fitness Studio Booking API"
API_V1_STR="/api/v1"
DATABASE_URL="sqlite:///./fitness_studio.db"
SECRET_KEY="change-this-in-production-to-a-secure-random-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Running the Application

Start the local development server using Uvicorn:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once started:
- **Interactive API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Documentation (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Testing via Swagger UI (`/docs`)

You can test all endpoints directly in your browser using Swagger UI at `http://127.0.0.1:8000/docs`:

### Step 1: Health Check (`GET /health`)
- Open the endpoint and click **Try it out** -> **Execute**.
- **Expected Status:** `200 OK`
- **Response:**
  ```json
  {
    "status": "healthy",
    "app_name": "Fitness Studio Booking API",
    "version": "1.0.0",
    "timestamp": "2026-10-14T11:45:00.000000+05:30"
  }
  ```

### Step 2: Register a New User (`POST /signup`)
- Send a request body with an email and password (minimum 6 characters):
  ```json
  {
    "email": "user@example.com",
    "password": "Password123"
  }
  ```
- **Expected Status:** `201 Created`
- **Response:**
  ```json
  {
    "email": "user@example.com",
    "id": 1,
    "created_at": "2026-10-14T06:15:00Z",
    "updated_at": "2026-10-14T06:15:00Z"
  }
  ```
- If you submit the same email again, the API returns `409 Conflict`.

### Step 3: Log In (`POST /login`)
- Send the registered credentials:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123"
  }
  ```
- **Expected Status:** `200 OK`
- **Response:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```
- Copy the `access_token` value.
- Click the **Authorize** button (lock icon at the top right of Swagger UI), paste the token into the value box, and click **Authorize**. All subsequent protected requests will include this Bearer token automatically.

### Step 4: Create a Fitness Class (`POST /classes`)
- Requires authorization token.
- Enter a class schedule (start time must be in the future):
  ```json
  {
    "name": "Power Vinyasa Yoga",
    "instructor": "Aarav Sharma",
    "capacity": 15,
    "start_time": "2026-10-20T09:00:00+05:30"
  }
  ```
- **Expected Status:** `201 Created`
- **Response:**
  ```json
  {
    "id": 1,
    "name": "Power Vinyasa Yoga",
    "instructor": "Aarav Sharma",
    "capacity": 15,
    "start_time": "2026-10-20T09:00:00+05:30",
    "start_time_ist": "2026-10-20T09:00:00+05:30",
    "booked_slots": 0,
    "available_slots": 15,
    "created_at": "2026-10-14T11:45:00+05:30"
  }
  ```

### Step 5: List Upcoming Classes (`GET /classes`)
- Public endpoint (no token required).
- Returns all classes scheduled in the future with dynamically computed `booked_slots` and `available_slots`.
- Classes that have already passed are automatically filtered out.

### Step 6: Book a Slot (`POST /book`)
- Requires authorization token.
- Provide the `class_id` of the class you want to attend:
  ```json
  {
    "class_id": 1
  }
  ```
- **Expected Status:** `201 Created`
- **Response:**
  ```json
  {
    "id": 1,
    "user_id": 1,
    "class_id": 1,
    "booked_at": "2026-10-14T11:46:00+05:30",
    "booked_at_ist": "2026-10-14T11:46:00+05:30",
    "fitness_class": {
      "id": 1,
      "name": "Power Vinyasa Yoga",
      "instructor": "Aarav Sharma",
      "start_time": "2026-10-20T09:00:00+05:30",
      "start_time_ist": "2026-10-20T09:00:00+05:30",
      "capacity": 15
    }
  }
  ```
- Trying to book the same class again returns `409 Conflict`.
- Trying to book a full class returns `400 Bad Request`.

### Step 7: View Your Bookings (`GET /bookings`)
- Requires authorization token.
- Returns only the bookings belonging to the currently authenticated user.

---

## Running Automated Tests

The project includes an automated test suite written with `pytest`. Tests run against an isolated in-memory SQLite database (`sqlite:///:memory:`), so running tests does not modify or corrupt the local development database.

Run the tests using:

```powershell
.venv\Scripts\pytest -v
```

### What the Tests Verify
- **Authentication (`tests/test_auth.py`):**
  - Health check endpoint response.
  - Successful user signup and password hashing verification.
  - Rejection of duplicate emails (`409 Conflict`).
  - Validation of malformed emails and short passwords (`422 Unprocessable Entity`).
  - Successful login and JWT issuance.
  - Rejection of invalid passwords and non-existent accounts (`401 Unauthorized`).
  - Handling of missing, expired, and corrupted JWT tokens.
- **Classes and Bookings (`tests/test_classes_and_bookings.py`):**
  - Requiring authentication to create classes.
  - Rejecting past class start times and invalid capacity (zero or negative).
  - Timezone handling between UTC and IST.
  - Automatic exclusion of past classes from the upcoming class listing.
  - Slot reservation and dynamic calculation of `available_slots`.
  - Handling non-existent class IDs (`404 Not Found`).
  - Preventing duplicate bookings by the same user (`409 Conflict`).
  - Rejecting bookings when a class is at full capacity (`400 Bad Request`).
  - Strict isolation ensuring users only see their own bookings.
  - Rejecting booking attempts for classes that have already started.
  - Concurrency test: verifying that when two users compete for the final remaining slot, exactly one succeeds and overbooking is prevented.

---

## Known Limitations

1. **Database engine (SQLite):** SQLite is well-suited for development and assignments, but uses file-level locking for writes. For higher-concurrency production deployments, migrating to PostgreSQL with a connection pool (e.g., PgBouncer) would be recommended.
2. **Class creation access control:** Currently, any authenticated user can create classes through `POST /classes`. In a production fitness studio app, this endpoint would be restricted to an admin or instructor role.
3. **Cancellations and rescheduling:** The current scope supports creating classes and booking slots. Booking cancellation (`DELETE /bookings/{id}`) and class rescheduling are not yet implemented.
