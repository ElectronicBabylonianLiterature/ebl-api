"""Shared management errors and UTC audit timestamps."""

from datetime import datetime, timezone


class MediaConflictError(Exception):
    pass


class MediaPermissionError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
