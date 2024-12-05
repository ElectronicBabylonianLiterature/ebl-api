from abc import ABC, abstractmethod

from ebl.dossier.domain.dossier_record import (
    DossierRecord,
)


class DossierRepository(ABC):
    @abstractmethod
    def fetch(self, name: str) -> DossierRecord: ...

    @abstractmethod
    def create(self, dossier_record: DossierRecord) -> str: ...
