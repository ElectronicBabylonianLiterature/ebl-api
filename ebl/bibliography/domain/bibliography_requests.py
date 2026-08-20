"""Request contracts for the internal bibliography editor routes.

`CSL_JSON_SCHEMA` describes a **stored** bibliography entry. A stored entry and
an HTTP request body are not the same object, and validating one against the
other produced two defects:

* ordinary create accepted `aliases`, `citationKey`, `deprecated` and
  `redirectTo`, so it was a second, unauthenticated identity-management
  endpoint;
* a metadata update carrying `deprecated` failed with
  `'redirectTo' is a required property`, a stored-entry invariant reported as
  if the client owned the lifecycle, before the application could say the
  submitted state simply disagrees with the stored state.

So the contracts are separated by what the caller is allowed to decide:

* create — client-editable CSL metadata only; identity is not the client's to
  supply, so the server-owned properties are absent from the contract;
* metadata update — the same field *shapes* the stored entry uses, including
  the server-owned ones, because the editor round-trips a previous `GET`. It
  deliberately drops the lifecycle rule: whether `deprecated` may change is a
  question about stored state, answered by the application as a conflict, not
  a question about the request body.

Neither contract weakens `CSL_JSON_SCHEMA` itself. Stored entries keep the
`deprecated` ⇒ `redirectTo` invariant, and the trusted identity operation
still builds only canonical lifecycle state. Both are built from deep copies
so no route can mutate the stored schema or another route's contract.
"""

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


INTERNAL_CREATE_JSON_SCHEMA = {
    "type": "object",
    "description": (
        "Ordinary internal bibliography creation. Accepts a client-supplied "
        "canonical id and client-editable CSL metadata. Identity and lifecycle "
        "state belong to POST /bibliography/{id}/identity."
    ),
    "properties": _client_editable_properties(),
    "required": ["type", "id"],
    "additionalProperties": False,
}

INTERNAL_METADATA_UPDATE_JSON_SCHEMA = {
    "type": "object",
    "description": (
        "Ordinary internal metadata edit. Server-owned fields are accepted in "
        "the body only so the editor can round-trip a previous GET; a value "
        "that disagrees with stored state is a conflict, not a mutation."
    ),
    "properties": _stored_properties(),
    "required": ["type", "id"],
    "additionalProperties": False,
}
