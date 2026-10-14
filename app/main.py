"""Main FastAPI application entrypoint.

Configures application lifecycle (lifespan), initializes database tables,
and mounts endpoint routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.database import Base, engine
# Import models to ensure they are registered with Base metadata before table creation
import app.models  # noqa: F401
from app.routers import auth, health, fitness_classes, bookings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Executes startup and shutdown tasks:
    - Automatically creates database tables on startup if they don't already exist.
    """
    # Startup: create SQLite database tables defined by SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    yield
    # Clean-up actions on application shutdown can be placed here


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Fitness Studio Booking API built with FastAPI, SQLite, and SQLAlchemy. "
        "Provides user signup, authentication with JWT, fitness class scheduling, "
        "and class slot bookings."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    """Redirects the root URL to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(fitness_classes.router)
app.include_router(bookings.router)

