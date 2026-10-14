"""Date and time utilities for standardized UTC storage and IST representation.

Ensures all datetimes in the database are stored as timezone-aware UTC timestamps,
while supporting seamless Indian Standard Time (IST, UTC+05:30) input and formatted output.
"""

from datetime import datetime, timezone, timedelta

# Indian Standard Time (IST) offset is fixed at UTC+05:30
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def get_current_utc() -> datetime:
    """Returns the current timestamp as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def get_current_ist() -> datetime:
    """Returns the current timestamp as a timezone-aware IST datetime."""
    return datetime.now(IST)


def ensure_utc(dt: datetime) -> datetime:
    """Normalizes any datetime to a timezone-aware UTC datetime.

    - If dt is naive (no timezone attached): it is assumed to be in IST
      (UTC+05:30) as required by the fitness studio's operational context,
      and converted to UTC.
    - If dt is already timezone-aware: it is converted to UTC.

    Args:
        dt: Input datetime, naive or timezone-aware.

    Returns:
        Timezone-aware datetime in UTC.
    """
    if dt.tzinfo is None:
        # Assume input was given in local Indian Standard Time
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(timezone.utc)


def to_utc_aware(dt: datetime) -> datetime:
    """Ensures a datetime retrieved from SQLite has timezone.utc attached.

    Since SQLite stores datetimes as naive strings, values retrieved from
    the database may have tzinfo=None. This utility ensures it is safely
    timezone-aware in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_ist(dt: datetime) -> datetime:
    """Converts any datetime to Indian Standard Time (IST, UTC+05:30).

    Args:
        dt: Input datetime.

    Returns:
        Timezone-aware datetime in IST.
    """
    return to_utc_aware(dt).astimezone(IST)


def format_iso_ist(dt: datetime) -> str:
    """Returns an ISO 8601 formatted string in IST with timezone offset (+05:30).

    Example output: '2026-10-15T18:00:00+05:30'
    """
    return to_ist(dt).isoformat()
