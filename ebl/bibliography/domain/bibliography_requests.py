from copy import deepcopy
from typing import Any, cast

from ebl.bibliography.domain.bibliography_entry import (
    CSL_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)


def _stored_properties() -> dict[str, Any]:
    return deepcopy(cast(dict[str, Any], CSL_JSON_SCHEMA["properties"]))


def _client_editable_properties() -> dict[str, Any]:
    return {
        name: schema
        for name, schema in _stored_properties().items()
        if name not in SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    }


_internal_create_properties = _client_editable_properties()
_internal_create_properties["id"] = {
    **_internal_create_properties["id"],
    "pattern": r"^(?![\s\S]*[/\x00-\x1f\x7f])[\s\S]+$",
}

INTERNAL_CREATE_JSON_SCHEMA = {
    "type": "object",
    "description": (
        "Ordinary internal bibliography creation. Accepts a client-supplied "
        "canonical id and client-editable CSL metadata. Identity and lifecycle "
        "state belong to POST /bibliography/{id}/identity."
    ),
    "properties": _internal_create_properties,
    "required": ["type", "id"],
    "additionalProperties": False,
}

INTERNAL_METADATA_UPDATE_JSON_SCHEMA = {
    "type": "object",
    "description": (
        "Ordinary internal metadata edit. Server-owned fields are accepted in "
        "the body only so the editor can round-trip a previous GET; a value "
        "that disagrees with stored state is a conflict, not a mutation. The "
        "id comes from the URL, and additional properties are tolerated at the "
        "schema layer because a GET body carries persisted keys outside the "
        "CSL schema (legacy documents); the application rejects any that are "
        "not an exact round-trip."
    ),
    "properties": _stored_properties(),
    "required": ["type"],
    "additionalProperties": True,
}

DUPLICATE_CANDIDATE_JSON_SCHEMA = {
    "type": "object",
    "description": (
        "Duplicate-detection probe. Client-editable CSL metadata only, like "
        "create: identity fields play no role in detection, and the stored "
        "lifecycle invariant does not apply to a proposed entry that is never "
        "persisted. A partner-style id is accepted the same way the partner "
        "create/update contract accepts one."
    ),
    "properties": {
        **_client_editable_properties(),
        "id": {"type": "string"},
    },
    "required": ["type"],
    "additionalProperties": False,
}
