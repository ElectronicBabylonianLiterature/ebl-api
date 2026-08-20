"""Validating an intended bibliography identity state before it is persisted.

Redirect safety is checked by resolving the prospective entry through the same
`follow_bibliography_redirect` used at read time, with the record under change
substituted for its stored version. Reusing the reader keeps one redirect
policy: the depth limit, the cycle rule and the missing-target rule cannot
drift apart from what resolution actually enforces.

A rejected request is reported as `DataError` (HTTP 422) rather than the
reader's `NotFoundError`/`DuplicateError`, because it is the submitted
identity state that is unacceptable, not the addressed record.
"""

from copy import deepcopy
from typing import Any, Callable, Mapping

from ebl.bibliography.application.redirect_resolution import (
    follow_bibliography_redirect,
)
from ebl.errors import DataError, DuplicateError, NotFoundError


def validate_identity_state(
    entry: Mapping[str, Any], query_by_id: Callable[[str], dict]
) -> None:
    _validate_tombstone(entry)
    _validate_redirect(entry, query_by_id)


def _validate_tombstone(entry: Mapping[str, Any]) -> None:
    id_ = entry["id"]
    redirect_to = entry.get("redirectTo")
    if entry.get("deprecated"):
        if not isinstance(redirect_to, str) or not redirect_to:
            raise DataError(
                f"Bibliography entry {id_} cannot be deprecated without a "
                "redirect target."
            )
        if redirect_to == id_:
            raise DataError(f"Bibliography entry {id_} cannot redirect to itself.")
    elif redirect_to:
        raise DataError(
            f"Bibliography entry {id_} cannot have a redirect target while "
            "it is not deprecated."
        )


def _validate_redirect(
    entry: Mapping[str, Any], query_by_id: Callable[[str], dict]
) -> None:
    if not entry.get("deprecated"):
        return

    prospective_entry = deepcopy(dict(entry))

    def query(id_: str) -> dict:
        return (
            deepcopy(prospective_entry)
            if id_ == prospective_entry["id"]
            else query_by_id(id_)
        )

    try:
        follow_bibliography_redirect(deepcopy(prospective_entry), query)
    except (DuplicateError, NotFoundError) as error:
        raise DataError(str(error)) from error
