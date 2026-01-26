from typing import Sequence
from abc import ABC, abstractmethod

from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)


class AfoRegisterRepository(ABC):
    @abstractmethod
    def create(self, afo_register_record: AfoRegisterRecord) -> str: ...

    @abstractmethod
    def search(self, query, *args, **kwargs) -> Sequence[AfoRegisterRecord]: ...

    @abstractmethod
    def search_by_texts_and_numbers(
        self, query_list: Sequence[str], *args, **kwargs
    ) -> Sequence[AfoRegisterRecord]: ...

    @abstractmethod
    def search_suggestions(
        self, text_query: str, *args, **kwargs
    ) -> Sequence[AfoRegisterRecordSuggestion]: ...
