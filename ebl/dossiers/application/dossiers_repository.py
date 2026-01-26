from typing import Sequence, Optional
from abc import ABC, abstractmethod

from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)


class DossiersRepository(ABC):
    @abstractmethod
    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]:
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        provenance: Optional[str] = None,
        script_period: Optional[str] = None,
    ) -> Sequence[DossierRecord]:
        pass

    @abstractmethod
    def create(self, dossier_record: DossierRecord) -> str:
        pass
