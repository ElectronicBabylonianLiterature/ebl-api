from typing import Sequence
from abc import ABC, abstractmethod

from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord


class AfoRegisterRepository(ABC):
    @abstractmethod
    def search(self, query, *args, **kwargs) -> Sequence[AfoRegisterRecord]:
        ...

    @abstractmethod
    def create(self, afo_register_record: AfoRegisterRecord) -> str:
        ...
