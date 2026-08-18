from copy import deepcopy
from typing import Any, Mapping, cast

from ebl.bibliography.domain.bibliography_entry import (
    CSL_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)

CLIENT_EDITABLE_BIBLIOGRAPHY_FIELDS = (
    frozenset(cast(dict[str, Any], CSL_JSON_SCHEMA["properties"]))
    - SERVER_OWNED_BIBLIOGRAPHY_FIELDS
)


def strip_server_owned_fields(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in entry.items()
        if key not in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    }


def client_editable_fields(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in entry.items()
        if key in CLIENT_EDITABLE_BIBLIOGRAPHY_FIELDS
    }


def stored_server_owned_fields(stored_entry: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(
        {
            field: stored_entry[field]
            for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
            if field in stored_entry
        }
    )


def stored_preserved_fields(stored_entry: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(
        {
            key: value
            for key, value in stored_entry.items()
            if key not in CLIENT_EDITABLE_BIBLIOGRAPHY_FIELDS
        }
    )


def preserve_server_owned_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        **strip_server_owned_fields(entry),
        **stored_server_owned_fields(stored_entry),
    }


def preserve_persisted_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        **client_editable_fields(entry),
        **stored_preserved_fields(stored_entry),
    }


def changed_server_owned_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> list[str]:
    return sorted(
        field
        for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
        if field in entry and entry[field] != stored_entry.get(field)
    )
