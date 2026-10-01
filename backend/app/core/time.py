"""Calendar dates and timestamp-derived business dates use UTC throughout the API."""
from datetime import datetime, timezone


def utc_today():
    return datetime.now(timezone.utc).date()
