from typing import Dict, Iterable, List, Optional, Sequence, Set

from ebl.bibliography.application.redirect_resolution import MAX_REDIRECT_DEPTH
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


def resolved_document(document: dict, fetched: Dict[str, dict]) -> Optional[dict]:
    seen: Set[str] = set()
    redirects_followed = 0
    while document.get("deprecated", False):
        current_id = document.get("id")
        target = redirect_target_of(document)
        if target is None or not isinstance(current_id, str):
            return None
        if current_id in seen or target in seen:
            return None
        if redirects_followed >= MAX_REDIRECT_DEPTH:
            return None
        seen.add(current_id)
        if target not in fetched:
            return None
        document = fetched[target]
        redirects_followed += 1
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


def bibliography_documents_of(
    items: Sequence[FragmentQuerySummary], repository: BibliographyRepository
) -> Dict[str, dict]:
    bibliography_ids = bibliography_ids_of(items)
    documents = documents_by_id(bibliography_ids, repository)
    fetched = dict(documents)
    requested = set(bibliography_ids)
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
