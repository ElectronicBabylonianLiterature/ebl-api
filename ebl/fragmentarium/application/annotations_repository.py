from abc import ABC, abstractmethod
from typing import List, Sequence

from ebl.fragmentarium.domain.annotation import Annotations
from ebl.transliteration.domain.museum_number import MuseumNumber


class AnnotationsRepository(ABC):
    @abstractmethod
    def find_by_sign(self, sign: str) -> Sequence[Annotations]: ...

    @abstractmethod
    def query_by_museum_number(self, number: MuseumNumber) -> Annotations: ...

    @abstractmethod
    def retrieve_all_non_empty(self) -> List[Annotations]: ...

    @abstractmethod
    def create_or_update(self, annotations: Annotations) -> None: ...
