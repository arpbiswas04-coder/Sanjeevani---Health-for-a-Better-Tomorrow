"""
Sanjeevani Grid - Shared Types & Validation Utilities
ai/common/types.py

Defines the canonical risk levels and standard identifier/timestamp validators
mandated by docs/api/API_CONVENTIONS.md.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Union
import uuid

try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)

# Canonical Risk Levels mandated by docs/api/API_CONVENTIONS.md (Section 5)
class RiskLevel(StrEnum):
    """
    Canonical risk levels for Sanjeevani Grid forecasting, triage, and supply-chain resilience.
    Values inherit from StrEnum for JSON serialization and Pydantic schema validation.
    """
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


_UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_uuid_v4(val: Any) -> bool:
    """Check if the provided value is a valid UUID v4 string or UUID instance."""
    if isinstance(val, uuid.UUID):
        return val.version == 4
    if not isinstance(val, str):
        return False
    val = val.strip()
    if not _UUID_V4_PATTERN.match(val):
        return False
    try:
        parsed = uuid.UUID(val, version=4)
        return parsed.version == 4
    except (ValueError, AttributeError):
        return False


def ensure_uuid_v4(val: Any) -> str:
    """
    Validate and return canonical lowercase UUID v4 string.
    Raises ValueError if input is not a valid UUID v4.
    """
    if isinstance(val, uuid.UUID) and val.version == 4:
        return str(val).lower()
    if isinstance(val, str) and is_valid_uuid_v4(val):
        return str(uuid.UUID(val.strip(), version=4)).lower()
    raise ValueError(f"Invalid UUID v4 identifier: {val!r}")


def is_valid_utc_iso8601(val: Any) -> bool:
    """
    Verify whether input string is an ISO-8601 formatted timestamp explicitly in UTC.
    Accepts trailing 'Z' or zero offset '+00:00'.
    """
    if not isinstance(val, str):
        return False
    val_clean = val.strip()
    if not val_clean:
        return False

    # Check for UTC indicators
    has_z = val_clean.endswith("Z") or val_clean.endswith("z")
    has_zero_offset = val_clean.endswith("+00:00") or val_clean.endswith("-00:00")
    if not (has_z or has_zero_offset):
        return False

    try:
        # Normalize trailing Z to +00:00 for fromisoformat in older pythons
        iso_str = val_clean[:-1] + "+00:00" if (has_z and not val_clean.endswith("+00:00")) else val_clean
        dt = datetime.fromisoformat(iso_str)
        return dt.tzinfo is not None and dt.utcoffset() == timezone.utc.utcoffset(dt)
    except (ValueError, TypeError):
        return False


def ensure_utc_iso8601(val: Union[str, datetime]) -> str:
    """
    Ensure input is converted to a canonical UTC ISO-8601 string ending in 'Z'.
    Raises ValueError if input cannot be validated as a UTC timestamp.
    """
    if isinstance(val, datetime):
        if val.tzinfo is None:
            raise ValueError(f"Naive datetime provided without UTC timezone: {val!r}")
        dt_utc = val.astimezone(timezone.utc)
        return format_utc_iso8601(dt_utc)
    
    if isinstance(val, str):
        if not is_valid_utc_iso8601(val):
            raise ValueError(f"Invalid UTC ISO-8601 timestamp: {val!r}")
        # Normalize to canonical YYYY-MM-DDTHH:MM:SSZ format
        clean_str = val.strip()
        iso_str = clean_str[:-1] + "+00:00" if (clean_str.endswith("Z") or clean_str.endswith("z")) else clean_str
        dt = datetime.fromisoformat(iso_str).astimezone(timezone.utc)
        return format_utc_iso8601(dt)

    raise ValueError(f"Expected datetime or str for UTC timestamp, got {type(val).__name__}")


def format_utc_iso8601(dt: datetime) -> str:
    """Format timezone-aware UTC datetime into standard ISO 8601 string ending in 'Z'."""
    if dt.tzinfo is None:
        raise ValueError("Cannot format naive datetime without timezone as UTC")
    dt_utc = dt.astimezone(timezone.utc)
    if dt_utc.microsecond > 0:
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc_iso8601() -> str:
    """Return the current system time in standard UTC ISO-8601 format."""
    return format_utc_iso8601(datetime.now(timezone.utc))
