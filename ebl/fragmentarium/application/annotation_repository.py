from abc import ABC, abstractmethod

from ebl.fragmentarium.domain.annotation import Annotations


class AnnotationRepository(ABC):
    @abstractmethod
    def query_by_fragment_number(self, fragment_number) -> Annotations:
        ...

    @abstractmethod
    def create_or_update(self, annotations: Annotations) -> None:
        ...
