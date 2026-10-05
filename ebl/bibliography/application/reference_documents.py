from typing import Dict, Iterable, List, Optional, Sequence, Set

from ebl.bibliography.application.redirect_resolution import MAX_REDIRECT_DEPTH
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.partner_identity import normalize_partner_id


def redirect_target_of(document: dict) -> Optional[str]:
    target = document.get("redirectTo") if document.get("deprecated") else None
    return target if isinstance(target, str) and target else None


def pending_targets_of(documents: Iterable[dict], requested: Set[str]) -> List[str]:
    targets = dict.fromkeys(
        target
        for document in documents
        if (target := redirect_target_of(document)) and target not in requested
    )
    return list(targets)


def resolved_document(document: dict, fetched: Dict[str, dict]) -> Optional[dict]:
    seen: Set[str] = set()
    while document.get("deprecated", False):
        current_id = document.get("id")
        target = redirect_target_of(document)
        if not isinstance(current_id, str):
            return None
        if target is None:
            return document
        if target in seen or len(seen) >= MAX_REDIRECT_DEPTH or target not in fetched:
            return None
        seen.add(current_id)
        document = fetched[target]
    return document


def documents_by_id(
    ids: Sequence[str], repository: BibliographyRepository
) -> Dict[str, dict]:
    if not ids:
        return {}
    returned = {
        document["id"]: document for document in repository.query_by_ids(list(ids))
    }
    return {id_: returned[id_] for id_ in ids if id_ in returned}


def lookup_document(id_: str, candidates: Sequence[dict]) -> Optional[dict]:
    citation_matches = [
        entry for entry in candidates if entry.get("citationKey") == id_
    ]
    normalized = normalize_partner_id(id_)
    alias_matches = [
        entry
        for entry in candidates
        if any(
            isinstance(alias, dict)
            and (
                alias.get("value") == id_
                or bool(normalized and alias.get("normalizedValue") == normalized)
            )
            for alias in (
                entry["aliases"] if isinstance(entry.get("aliases"), list) else []
            )
        )
    ]
    matches = citation_matches or alias_matches
    unique = {entry["id"]: entry for entry in matches}
    return next(iter(unique.values())) if len(unique) == 1 else None


def bibliography_documents_by_lookup(
    ids: Sequence[str], repository: BibliographyRepository
) -> Dict[str, dict]:
    ids = list(dict.fromkeys(ids))
    documents = documents_by_id(ids, repository)
    missing = [id_ for id_ in ids if id_ not in documents]
    if missing:
        candidates = repository.query_by_lookup_values(missing)
        for id_ in missing:
            if document := lookup_document(id_, candidates):
                documents[id_] = document
    fetched = {document["id"]: document for document in documents.values()}
    requested = set(ids) | set(fetched)
    batch = documents
    for _ in range(MAX_REDIRECT_DEPTH):
        targets = pending_targets_of(batch.values(), requested)
        if not targets:
            break
        requested.update(targets)
        batch = documents_by_id(targets, repository)
        fetched.update(batch)
    resolved = {
        id_: resolved_document(document, fetched) for id_, document in documents.items()
    }
    return {id_: document for id_, document in resolved.items() if document is not None}


def _normalized_references(record: dict) -> List[dict]:
    record["references"] = record.get("references") or []
    return record["references"]


def hydrate_reference_documents(
    records: Sequence[dict], repository: BibliographyRepository
) -> None:
    references = [
        reference for record in records for reference in _normalized_references(record)
    ]
    documents = bibliography_documents_by_lookup(
        [reference["id"] for reference in references], repository
    )
    for reference in references:
        reference["document"] = documents.get(reference["id"])
