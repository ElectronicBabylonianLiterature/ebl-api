from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.reference_documents import (
    bibliography_documents_by_lookup,
)
from ebl.bibliography.application.reference_search_identities import (
    ReferenceSearchIdentities,
    identities_of,
    requested_identities,
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


def _incoming_identities(
    canonical: dict, repository: BibliographyRepository
) -> ReferenceSearchIdentities:
    identities = ReferenceSearchIdentities()
    for incoming in _incoming_entries(canonical, repository):
        identities = identities.merge(identities_of(incoming))
        if len(identities.stored_reference_values()) > MAX_REFERENCE_SEARCH_VALUES:
            raise DataError("Bibliography reference search exceeds identity limit.")
    return identities


def _resolved_identities(
    id_: str, repository: BibliographyRepository
) -> ReferenceSearchIdentities:
    entry = _lookup_entry(id_, repository)
    canonical = follow_bibliography_redirect(entry, repository.query_by_id)
    candidates = requested_identities(id_, entry).merge(
        _incoming_identities(canonical, repository)
    )
    resolved = bibliography_documents_by_lookup(
        candidates.stored_reference_values(), repository
    )
    return candidates.keep(
        lambda value: value in resolved and resolved[value]["id"] == canonical["id"]
    )


def equivalent_reference_identities(
    id_: str, repository: BibliographyRepository
) -> ReferenceSearchIdentities:
    if not isinstance(id_, str) or not id_:
        raise DataError("Bibliography ID must be a non-empty string.")
    try:
        return _resolved_identities(id_, repository)
    except (NotFoundError, DuplicateError):
        return ReferenceSearchIdentities(unresolved_reference_ids=(id_,))
