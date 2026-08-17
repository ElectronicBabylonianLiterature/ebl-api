from typing import Any, Mapping

from ebl.bibliography.domain.bibliography_entry import (
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)


def strip_server_owned_fields(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in entry.items()
        if key not in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    }


def stored_server_owned_fields(stored_entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field: stored_entry[field]
        for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
        if field in stored_entry
    }


def preserve_server_owned_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        **strip_server_owned_fields(entry),
        **stored_server_owned_fields(stored_entry),
    }
