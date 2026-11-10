"""Shared management errors and UTC audit timestamps."""

from datetime import datetime, timezone


class MediaConflictError(Exception):
    pass


class MediaPermissionError(Exception):
    pass


class MediaRevisionRequiredError(Exception):
    """The operation requires the revision the caller reviewed (If-Match)."""


class MediaRevisionConflictError(Exception):
    """The media changed after the caller loaded the revision it sent."""

    def __init__(self, expected: int, current: int) -> None:
        super().__init__("Media changed since it was loaded; reload and review again.")
        self.expected = expected
        self.current = current


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
