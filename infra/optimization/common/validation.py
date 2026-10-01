"""Strict JSON validation, without silently coercing quantities or IDs."""

import math
from typing import Any


class ValidationError(ValueError):
    """A caller supplied an invalid request or policy."""


def object_fields(
    value: Any, *, required: set[str], optional: set[str], path: str
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing:
        raise ValidationError(f"{path} missing fields: {', '.join(sorted(missing))}")
    if extra:
        raise ValidationError(f"{path} contains unsupported fields")
    return value


def identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValidationError(f"{path} must be a nonempty string without outer whitespace")
    if len(value) > 128 or any(ord(char) < 32 for char in value):
        raise ValidationError(f"{path} contains invalid characters or exceeds 128 characters")
    return value


def integer(value: Any, path: str, minimum: int | None = 0) -> int:
    if type(value) is not int:
        raise ValidationError(f"{path} must be an integer")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{path} must be at least {minimum}")
    return value


def nonnegative_number(value: Any, path: str) -> float:
    if type(value) not in (int, float):
        raise ValidationError(f"{path} must be a finite nonnegative number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValidationError(f"{path} must be a finite nonnegative number") from exc
    if not math.isfinite(result) or result < 0:
        raise ValidationError(f"{path} must be a finite nonnegative number")
    return result

