from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from ebl.fragmentarium.domain.annotation import Annotations
from ebl.transliteration.domain.museum_number import MuseumNumber


class AnnotationsRepository(ABC):
    @abstractmethod
    def create_indexes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_sign(
        self,
        sign: str,
        centroids_only: bool = False,
        include_unclustered: bool = False,
        cluster_id: Optional[str] = None,
        script_filter: Optional[str] = None,
    ) -> Sequence[Annotations]:
        raise NotImplementedError

    @abstractmethod
    def query_by_museum_number(self, number: MuseumNumber) -> Annotations:
        raise NotImplementedError

    @abstractmethod
    def retrieve_all_non_empty(self) -> List[Annotations]:
        raise NotImplementedError

    @abstractmethod
    def create_or_update(self, annotations: Annotations) -> None:
        raise NotImplementedError
