"""Splitting a bibliography entry into client-owned and server-owned parts.

Two helpers rebuild an entry from a submission plus stored state and are easy
to confuse:

* `preserve_server_owned_fields` keeps every submitted key except the
  server-owned ones and overlays the stored server-owned values. Callers that
  have already projected the submission to known metadata use it.
* `preserve_persisted_fields` keeps only submitted keys that are client
  editable and overlays everything else the stored document holds, including
  keys outside the CSL schema. The generic update uses it so unknown persisted
  fields survive an edit.

Two guards decide whether a metadata submission is allowed at all:

* `changed_server_owned_fields` -- a server-owned CSL field whose value
  disagrees with stored state (empty values and alias order do not count);
  the caller turns a non-empty result into a `409`.
* `reject_unknown_metadata_fields` -- a key outside the CSL vocabulary whose
  value is not an exact round-trip of stored state; raised as a `DataError`.
"""

from copy import deepcopy
from typing import Any, Mapping, cast

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
    """Collapse the shapes that mean "no identity state" onto one value.

    A round-tripped `GET` can carry `aliases: []`, `citationKey: ""`,
    `deprecated: False` or `redirectTo: None` for a field that is simply
    absent from storage; those are not a change. `aliases` is a logically
    unordered collection, so its order is not a change either.
    """
    if any(value == empty for empty in _EMPTY_SERVER_OWNED_VALUES):
        return None
    if field == "aliases":
        return sorted(tuple(sorted(alias.items())) for alias in value)
    return value


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
        if key not in _KNOWN_METADATA_UPDATE_FIELDS and value != stored_entry.get(key)
    )


def reject_unknown_metadata_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> None:
    """Refuse keys the metadata update does not recognise.

    A key outside the CSL vocabulary is accepted only when it round-trips a
    value already persisted (legacy documents carry such keys and the editor
    replays a `GET`). A new or changed value for one is not a metadata edit.
    """
    if unknown_fields := unknown_nonroundtrip_fields(entry, stored_entry):
        raise DataError(
            "Bibliography metadata update does not recognise: "
            f"{', '.join(unknown_fields)}. Only persisted values may be "
            "round-tripped for keys outside the CSL schema."
        )


def submitted_server_owned_fields(entry: Mapping[str, Any]) -> list[str]:
    return sorted(SERVER_OWNED_BIBLIOGRAPHY_FIELDS.intersection(entry))


def reject_submitted_server_owned_fields(entry: Mapping[str, Any]) -> None:
    """Refuse a client submission that carries server-owned identity state.

    Enforced here rather than only in the route schema so the invariant holds
    for any caller of the ordinary metadata creation path, not just HTTP.
    """
    if forbidden_fields := submitted_server_owned_fields(entry):
        raise DataError(
            "Bibliography creation may not include server-owned fields: "
            f"{', '.join(forbidden_fields)}. "
            "Use POST /bibliography/{id}/identity to manage identity state."
        )
