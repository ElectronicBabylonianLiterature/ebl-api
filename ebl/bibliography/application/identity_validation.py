"""Validating an intended bibliography identity state before it is persisted.

Redirect safety is checked by resolving the prospective entry through the same
`follow_bibliography_redirect` used at read time, with the record under change
substituted for its stored version. Reusing the reader keeps one redirect
policy: the depth limit, the cycle rule and the missing-target rule cannot
drift apart from what resolution actually enforces.

`_validate_redirect` only walks forward from the entry being changed, so a
change that is within the depth limit for that entry alone can still push an
existing predecessor -- a tombstone that already redirects to it, directly or
transitively -- over the limit. `_validate_inbound_chains` walks backward from
the entry through `query_by_redirect_target` and re-resolves every such
predecessor the same way, so that case is rejected too. It does not, and
cannot on its own, protect against two such changes racing on different
entries at once; that needs a lock or transaction spanning both records, which
this module does not provide.

A rejected request is reported as `DataError` (HTTP 422) rather than the
reader's `NotFoundError`/`DuplicateError`, because it is the submitted
identity state that is unacceptable, not the addressed record.
"""

from copy import deepcopy
from typing import Any, Callable, Mapping, Sequence

from ebl.bibliography.application.redirect_resolution import (
    follow_bibliography_redirect,
)
from ebl.errors import DataError, DuplicateError, NotFoundError


def validate_identity_state(
    entry: Mapping[str, Any],
    query_by_id: Callable[[str], dict],
    query_by_redirect_target: Callable[[str], Sequence[Mapping[str, Any]]],
) -> None:
    _validate_tombstone(entry)
    _validate_redirect(entry, query_by_id)
    _validate_inbound_chains(entry, query_by_id, query_by_redirect_target)


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


def _prospective_query(
    entry: Mapping[str, Any], query_by_id: Callable[[str], dict]
) -> Callable[[str], dict]:
    prospective_entry = deepcopy(dict(entry))

    def query(id_: str) -> dict:
        return (
            deepcopy(prospective_entry)
            if id_ == prospective_entry["id"]
            else query_by_id(id_)
        )

    return query


def _validate_redirect(
    entry: Mapping[str, Any], query_by_id: Callable[[str], dict]
) -> None:
    if not entry.get("deprecated"):
        return

    query = _prospective_query(entry, query_by_id)
    try:
        follow_bibliography_redirect(query(entry["id"]), query)
    except (DuplicateError, NotFoundError) as error:
        raise DataError(str(error)) from error


def _validate_inbound_chains(
    entry: Mapping[str, Any],
    query_by_id: Callable[[str], dict],
    query_by_redirect_target: Callable[[str], Sequence[Mapping[str, Any]]],
) -> None:
    if not entry.get("deprecated"):
        return

    query = _prospective_query(entry, query_by_id)
    visited: set[str] = set()
    frontier = [
        predecessor["id"] for predecessor in query_by_redirect_target(entry["id"])
    ]
    while frontier:
        predecessor_id = frontier.pop()
        if predecessor_id in visited:
            continue
        visited.add(predecessor_id)
        try:
            follow_bibliography_redirect(query(predecessor_id), query)
        except (DuplicateError, NotFoundError) as error:
            raise DataError(str(error)) from error
        frontier.extend(
            predecessor["id"]
            for predecessor in query_by_redirect_target(predecessor_id)
        )
