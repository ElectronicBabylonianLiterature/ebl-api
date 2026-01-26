from typing import Sequence
from abc import ABC, abstractmethod

from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)


class DossiersRepository(ABC):
    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]: ...

    @abstractmethod
    def search(self, query: str) -> Sequence[DossierRecord]: ...

    @abstractmethod
    def create(self, dossier_record: DossierRecord) -> str: ...
