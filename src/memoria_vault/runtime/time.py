"""Dependency-light UTC timestamp helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_z(value: datetime | None = None) -> str:
    """Return an ISO-8601 UTC timestamp with whole seconds and trailing ``Z``."""
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    current = current.astimezone(UTC).replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    """Return the current UTC time as ISO-8601 with trailing ``Z``."""
    return utc_z()


def parse_iso(value: str) -> datetime | None:
    """Parse an ISO-8601 timestamp string, returning ``None`` on failure."""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
