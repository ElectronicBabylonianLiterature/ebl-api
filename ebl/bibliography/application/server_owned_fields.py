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

`changed_server_owned_fields` reports which of them a submission disagrees with.
It compares `aliases` as an order-insensitive multiset, because no production
code reads an alias by position: lookup values are collected into a set, and
Mongo matches `aliases.normalizedValue` against the array as a whole. An editor
that re-serialises the list in another order has not changed the identity, so it
is not a conflict, while an alias added, removed, duplicated or edited still is.
Only the comparison is canonicalised — the stored order is never rewritten.
"""

import json
from copy import deepcopy
from typing import Any, Mapping, Sequence, cast

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


def canonical_aliases(aliases: Sequence[Any]) -> list[str]:
    return sorted(json.dumps(alias, sort_keys=True, default=str) for alias in aliases)


def comparable_server_owned_value(field: str, value: Any) -> Any:
    return (
        canonical_aliases(value)
        if field == "aliases" and isinstance(value, list)
        else value
    )


def changed_server_owned_fields(
    entry: Mapping[str, Any], stored_entry: Mapping[str, Any]
) -> list[str]:
    return sorted(
        field
        for field in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
        if field in entry
        and comparable_server_owned_value(field, entry[field])
        != comparable_server_owned_value(field, stored_entry.get(field))
    )
