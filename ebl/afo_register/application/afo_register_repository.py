from abc import ABC, abstractmethod

from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord


class AfoRegisterRepository(ABC):
    @abstractmethod
    def find(self, query, *args, **kwargs) -> AfoRegisterRecord:
        ...

    @abstractmethod
    def create(self, afo_register_record: AfoRegisterRecord) -> str:
        ...
