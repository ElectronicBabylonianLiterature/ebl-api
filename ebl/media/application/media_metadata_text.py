"""Strict text boundaries before staging binaries or encoding MongoDB records."""

from typing import Any

from ebl.errors import DataError


def valid_text(value: Any, maximum: int) -> bool:
    if not isinstance(value, str) or len(value) > maximum:
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


def validate_upload_metadata(data: dict) -> None:
    for field in (
        "originalFilename",
        "type",
        "caption",
        "rightsStatement",
        "permissionAttested",
    ):
        if not data.get(field):
            raise DataError(f"{field} is required.")
    if not data["caption"].strip() or not data["rightsStatement"].strip():
        raise DataError("Caption and rights statement must not be blank.")
    name = data["originalFilename"]
    if not name.strip() or len(name) > 255:
        raise DataError("Invalid original filename.")
    if any(character in name for character in ("/", "\\", "\x00", "\r", "\n")):
        raise DataError("Invalid original filename.")


def validate_review_metadata(data: dict) -> None:
    if set(data) - {"reason"}:
        raise DataError("Invalid review reason.")
    if "reason" in data and not valid_text(data["reason"], 4000):
        raise DataError("Invalid review reason.")
