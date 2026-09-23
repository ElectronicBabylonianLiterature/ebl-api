"""Validating an intended bibliography identity state before it is persisted."""

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
