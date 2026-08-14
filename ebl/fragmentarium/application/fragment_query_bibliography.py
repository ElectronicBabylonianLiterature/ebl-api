from typing import Dict, Iterable, List, Optional, Sequence, Set

from ebl.bibliography.application.bibliography import MAX_REDIRECT_DEPTH
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQuerySummary


def bibliography_ids_of(items: Sequence[FragmentQuerySummary]) -> List[str]:
    return list(
        dict.fromkeys(
            str(reference.id) for item in items for reference in item.references
        )
    )


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


def resolved_document(document: dict, fetched: Dict[str, dict]) -> dict:
    seen: Set[str] = set()
    while (target := redirect_target_of(document)) and target not in seen:
        seen.add(target)
        if target not in fetched:
            break
        document = fetched[target]
    return document


def documents_by_id(
    ids: Sequence[str], repository: BibliographyRepository
) -> Dict[str, dict]:
    return (
        {document["id"]: document for document in repository.query_by_ids(list(ids))}
        if ids
        else {}
    )


def bibliography_documents_of(
    items: Sequence[FragmentQuerySummary], repository: BibliographyRepository
) -> Dict[str, dict]:
    documents = documents_by_id(bibliography_ids_of(items), repository)
    fetched = dict(documents)
    requested = set(fetched)
    batch = documents
    for _ in range(MAX_REDIRECT_DEPTH):
        targets = pending_targets_of(batch.values(), requested)
        if not targets:
            break
        requested.update(targets)
        batch = documents_by_id(targets, repository)
        fetched.update(batch)
    return {
        id_: resolved_document(document, fetched) for id_, document in documents.items()
    }
