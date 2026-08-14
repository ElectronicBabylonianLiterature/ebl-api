from typing import Dict, List, Optional, Sequence

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


def resolved_document(document: dict, canonical: Dict[str, dict]) -> dict:
    target = redirect_target_of(document)
    return canonical.get(target, document) if target else document


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
    targets = dict.fromkeys(
        target
        for document in documents.values()
        if (target := redirect_target_of(document))
    )
    canonical = documents_by_id(list(targets), repository)
    return {
        id_: resolved_document(document, canonical)
        for id_, document in documents.items()
    }
