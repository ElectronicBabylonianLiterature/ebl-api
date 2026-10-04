"""Resolve bibliography lookup identities before searching stored references."""

from typing import Tuple

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.reference_documents import (
    bibliography_documents_by_lookup,
)
from ebl.bibliography.application.redirect_resolution import (
    MAX_REDIRECT_DEPTH,
    follow_bibliography_redirect,
)
from ebl.errors import DataError, DuplicateError, NotFoundError

MAX_REFERENCE_SEARCH_ENTRIES = 1000
MAX_REFERENCE_SEARCH_VALUES = 1000


def _lookup_entry(id_: str, repository: BibliographyRepository) -> dict:
    for lookup in (
        repository.query_by_id,
        repository.query_by_citation_key,
        repository.query_by_alias,
    ):
        try:
            return lookup(id_)
        except NotFoundError:
            continue
    raise NotFoundError(f"bibliography {id_} not found.")


def find_bibliography_entry(id_: str, repository: BibliographyRepository) -> dict:
    return follow_bibliography_redirect(
        _lookup_entry(id_, repository), repository.query_by_id
    )


def _incoming_entries(entry: dict, repository: BibliographyRepository):
    frontier = [entry]
    visited = set()
    depth = 0
    while frontier:
        for current in frontier:
            if current["id"] in visited:
                raise DuplicateError("Bibliography reverse redirect loop.")
            visited.add(current["id"])
            yield current
        incoming_entries = repository.query_by_redirect_targets(
            [current["id"] for current in frontier],
            limit=MAX_REFERENCE_SEARCH_ENTRIES + 1,
        )
        if len(incoming_entries) > MAX_REFERENCE_SEARCH_ENTRIES:
            raise DataError("Bibliography reference search exceeds entry limit.")
        incoming = [
            candidate
            for candidate in incoming_entries
            if candidate.get("deprecated", False)
        ]
        if incoming and depth >= MAX_REDIRECT_DEPTH:
            raise DuplicateError("Bibliography reverse redirect exceeds maximum depth.")
        if len(visited) + len(incoming) > MAX_REFERENCE_SEARCH_ENTRIES:
            raise DataError("Bibliography reference search exceeds entry limit.")
        frontier = incoming
        depth += 1


def equivalent_reference_ids(
    id_: str, repository: BibliographyRepository
) -> Tuple[str, ...]:
    """Include only identities that resolve to the requested canonical entry.

    Missing historical IDs retain exact matching. Broken redirects and ambiguous
    requested identities fail rather than combining unrelated publications.
    Unresolvable secondary aliases are omitted conservatively.
    """
    if not isinstance(id_, str) or not id_:
        raise DataError("Bibliography ID must be a non-empty string.")
    try:
        entry = _lookup_entry(id_, repository)
    except NotFoundError:
        return (id_,)
    canonical = follow_bibliography_redirect(entry, repository.query_by_id)
    candidates = {id_}
    for incoming in _incoming_entries(canonical, repository):
        candidates.update(bibliography_lookup_values(incoming))
        if len(candidates) > MAX_REFERENCE_SEARCH_VALUES:
            raise DataError("Bibliography reference search exceeds identity limit.")
    resolved = bibliography_documents_by_lookup(sorted(candidates), repository)
    return tuple(
        candidate
        for candidate in sorted(resolved)
        if resolved[candidate]["id"] == canonical["id"]
    )
