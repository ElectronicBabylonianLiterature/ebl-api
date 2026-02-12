from abc import ABC, abstractmethod
from typing import Sequence

from ebl.common.domain.provenance_model import ProvenanceRecord


class ProvenanceRepository(ABC):
    @abstractmethod
    def create(self, provenance: ProvenanceRecord) -> str:
        ...

    @abstractmethod
    def find_all(self) -> Sequence[ProvenanceRecord]:
        ...

    @abstractmethod
    def query_by_id(self, id_: str) -> ProvenanceRecord:
        ...

    @abstractmethod
    def query_by_long_name(self, long_name: str) -> ProvenanceRecord:
        ...

    @abstractmethod
    def query_by_abbreviation(self, abbreviation: str) -> ProvenanceRecord:
        ...

    @abstractmethod
    def update(self, provenance: ProvenanceRecord) -> None:
        ...

    @abstractmethod
    def find_children(self, parent_id: str) -> Sequence[ProvenanceRecord]:
        ...

    @abstractmethod
    def find_by_coordinates(
        self, latitude: float, longitude: float, radius_km: float
    ) -> Sequence[ProvenanceRecord]:
        ...
