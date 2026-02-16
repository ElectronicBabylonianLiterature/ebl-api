from typing import Sequence, Optional
from abc import ABC, abstractmethod

from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
    DossierRecordSuggestion,
)


class DossiersRepository(ABC):
    @abstractmethod
    def find_all(self) -> Sequence[DossierRecord]:
        raise NotImplementedError()

    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]:
        raise NotImplementedError()

    @abstractmethod
    def search(
        self,
        query: str,
        provenance: Optional[str] = None,
        script_period: Optional[str] = None,
    ) -> Sequence[DossierRecord]:
        raise NotImplementedError()

    @abstractmethod
    def search_suggestions(self, query: str) -> Sequence[DossierRecordSuggestion]:
        raise NotImplementedError()

    @abstractmethod
    def filter_by_fragment_criteria(
        self,
        provenance: Optional[str] = None,
        script_period: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> Sequence[DossierRecord]:
        raise NotImplementedError()

    @abstractmethod
    def create(self, dossier_record: DossierRecord) -> str:
        raise NotImplementedError()
