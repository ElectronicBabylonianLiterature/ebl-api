from typing import Any, Sequence
from abc import ABC, abstractmethod

from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)


class AfoRegisterRepository(ABC):
    @abstractmethod
    def create(self, afo_register_record: AfoRegisterRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    def search(
        self, query: Any, *args: Any, **kwargs: Any
    ) -> Sequence[AfoRegisterRecord]:
        raise NotImplementedError

    @abstractmethod
    def search_by_texts_and_numbers(
        self, query_list: Sequence[str], *args: Any, **kwargs: Any
    ) -> Sequence[AfoRegisterRecord]:
        raise NotImplementedError

    @abstractmethod
    def search_suggestions(
        self, text_query: str, *args: Any, **kwargs: Any
    ) -> Sequence[AfoRegisterRecordSuggestion]:
        raise NotImplementedError
