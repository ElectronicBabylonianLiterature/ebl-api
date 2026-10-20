from typing import Dict, List, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.reference_documents import (
    bibliography_documents_by_lookup,
)
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQuerySummary


def bibliography_ids_of(items: Sequence[FragmentQuerySummary]) -> List[str]:
    return list(
        dict.fromkeys(
            str(reference.id) for item in items for reference in item.references
        )
    )


def bibliography_documents_of(
    items: Sequence[FragmentQuerySummary], repository: BibliographyRepository
) -> Dict[str, dict]:
    return bibliography_documents_by_lookup(bibliography_ids_of(items), repository)
