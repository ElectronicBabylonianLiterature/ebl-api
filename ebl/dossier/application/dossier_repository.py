from abc import ABC, abstractmethod

from ebl.afo_register.domain.afo_register_record import (
    DossierRecord,
)

class AfoRegisterRepository(ABC):

    @abstractmethod
    def fetch(self, query, *args, **kwargs) -> DossierRecord: ...
