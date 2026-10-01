"""Timezone-aware timestamps for recommendation freshness checks."""

from datetime import datetime, timezone

from optimization.common.validation import ValidationError


def utc_timestamp(value, path):
    if not isinstance(value, str):
        raise ValidationError(f"{path} must be an ISO timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("missing timezone")
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValidationError(f"{path} must be an ISO timestamp with timezone") from exc


def utc_now(value=None):
    current = datetime.now(timezone.utc) if value is None else value
    if not isinstance(current, datetime) or current.tzinfo is None or current.utcoffset() is None:
        raise ValidationError("now must be a timezone-aware datetime")
    return current.astimezone(timezone.utc)
