from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Sequence

from ebl.bibliography.application.lookup_reservation import LookupReservationOperation
from ebl.errors import DuplicateError


class LookupValueReservationError(DuplicateError):
    def __init__(self, value: str):
        self.value = value
        super().__init__(f"Bibliography lookup value {value} is already reserved.")


class LookupValueInUseError(DuplicateError):
    def __init__(self, value: str):
        self.value = value
        super().__init__(f"Bibliography lookup value {value} is in use.")


class BibliographyRepository(ABC):
    @abstractmethod
    def create_indexes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def claim_lookup_values(
        self, operation: LookupReservationOperation, values: Sequence[str]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit_lookup_values(
        self, operation: LookupReservationOperation, now: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def release_pending_lookup_values(self, owner: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def retire_lookup_values(
        self, entry_id: str, values: Sequence[str], now: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def lookup_value_is_reserved(self, value: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def reconcile_lookup_reservations(self, now: datetime, limit: int = 100) -> int:
        raise NotImplementedError

    @abstractmethod
    def create(self, entry: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    def query_by_id(self, id_: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def query_by_citation_key(self, citation_key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def query_by_alias(self, alias: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def update(self, entry: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def query_page(self, after: Optional[str], limit: int) -> Sequence[Any]:
        raise NotImplementedError

    @abstractmethod
    def list_all_bibliography(self) -> Sequence[Any]:
        raise NotImplementedError
