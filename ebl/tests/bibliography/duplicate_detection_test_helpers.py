from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.lookup_reservation import LookupReservationOperation


class FakeBibliographyRepository(BibliographyRepository):
    def __init__(self, candidates: Sequence[dict[str, Any]]):
        self._candidates = candidates

    def create_indexes(self) -> None:
        raise NotImplementedError

    def claim_lookup_values(
        self, operation: LookupReservationOperation, values: Sequence[str]
    ) -> None:
        raise NotImplementedError

    def commit_lookup_values(
        self, operation: LookupReservationOperation, now: datetime
    ) -> None:
        raise NotImplementedError

    def release_pending_lookup_values(self, owner: str) -> None:
        raise NotImplementedError

    def retire_lookup_values(
        self, entry_id: str, values: Sequence[str], now: datetime
    ) -> None:
        raise NotImplementedError

    def lookup_value_is_reserved(self, value: str) -> bool:
        raise NotImplementedError

    def reconcile_lookup_reservations(self, now: datetime, limit: int = 100) -> int:
        raise NotImplementedError

    def create(self, entry: Any) -> str:
        raise NotImplementedError

    def query_by_id(self, id_: str) -> Any:
        raise NotImplementedError

    def query_by_citation_key(self, citation_key: str) -> Any:
        raise NotImplementedError

    def query_by_alias(self, alias: str) -> Any:
        raise NotImplementedError

    def query_by_redirect_target(self, id_: str) -> Sequence[Any]:
        raise NotImplementedError

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[Any]:
        raise NotImplementedError

    def update(
        self, entry: Any, expected_server_owned_fields: Mapping[str, Any]
    ) -> None:
        raise NotImplementedError

    def update_identity_fields(
        self, entry: Any, expected_server_owned_fields: Mapping[str, Any]
    ) -> None:
        raise NotImplementedError

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        return self._candidates

    def query_page(self, after: Optional[str], limit: int) -> Sequence[Any]:
        raise NotImplementedError

    def list_all_bibliography(self) -> Sequence[Any]:
        raise NotImplementedError


def entry(id_: str, **overrides: Any) -> dict[str, Any]:
    data = {
        "id": id_,
        "type": "article-journal",
        "title": "The Synergistic Activity of Thyroid Transcription Factor 1",
        "author": [{"given": "Stefania", "family": "Miccadei"}],
        "issued": {"date-parts": [[2002, 1, 1]]},
        "DOI": "10.1210/MEND.16.4.0808",
        "container-title": "Molecular Endocrinology",
        "volume": "2",
        "issue": "4",
        "page": "837-846",
    }
    data.update(overrides)
    return data
