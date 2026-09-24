import json
from copy import deepcopy
from typing import Any, Mapping, Sequence, cast

from ebl.bibliography.domain.bibliography_entry import (
    CSL_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)
from ebl.errors import DataError

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


_EMPTY_SERVER_OWNED_VALUES: tuple[Any, ...] = ([], "", False, None)


def _normalized_value(field: str, value: Any) -> Any:
    if any(value == empty for empty in _EMPTY_SERVER_OWNED_VALUES):
        return None
    if field == "aliases" and isinstance(value, list):
        return canonical_aliases(value)
    return value


def canonical_aliases(aliases: Sequence[Any]) -> list[str]:
    return sorted(json.dumps(alias, sort_keys=True, default=str) for alias in aliases)


def changed_server_owned_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> list[str]:
    return sorted(
        field
        for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
        if field in entry
        and _normalized_value(field, entry[field])
        != _normalized_value(field, stored_entry.get(field))
    )


_KNOWN_METADATA_UPDATE_FIELDS = (
    CLIENT_EDITABLE_BIBLIOGRAPHY_FIELDS | SERVER_OWNED_BIBLIOGRAPHY_FIELDS
)


def unknown_nonroundtrip_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> list[str]:
    return sorted(
        key
        for key, value in entry.items()
        if key not in _KNOWN_METADATA_UPDATE_FIELDS
        and (key not in stored_entry or value != stored_entry[key])
    )


def reject_unknown_metadata_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> None:
    if unknown_fields := unknown_nonroundtrip_fields(entry, stored_entry):
        raise DataError(
            "Bibliography metadata update does not recognise: "
            f"{', '.join(unknown_fields)}. Only persisted values may be "
            "round-tripped for keys outside the CSL schema."
        )


def submitted_server_owned_fields(entry: Mapping[str, Any]) -> list[str]:
    return sorted(SERVER_OWNED_BIBLIOGRAPHY_FIELDS.intersection(entry))


def reject_submitted_server_owned_fields(entry: Mapping[str, Any]) -> None:
    if forbidden_fields := submitted_server_owned_fields(entry):
        raise DataError(
            "Bibliography creation may not include server-owned fields: "
            f"{', '.join(forbidden_fields)}. "
            "Use POST /bibliography/{id}/identity to manage identity state."
        )
