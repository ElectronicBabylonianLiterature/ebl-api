from abc import ABC, abstractmethod

from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)


class DossiersRepository(ABC):
    @abstractmethod
    def fetch(self, id: str) -> DossierRecord: ...

    @abstractmethod
    def create(self, dossier_record: DossierRecord) -> str: ...
