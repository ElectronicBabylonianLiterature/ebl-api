from abc import ABC, abstractmethod
from typing import Sequence

from ebl.common.domain.provenance_model import ProvenanceRecord


class ProvenanceRepository(ABC):
    @abstractmethod
    def create(self, provenance: ProvenanceRecord) -> str:
        raise NotImplementedError()

    @abstractmethod
    def find_all(self) -> Sequence[ProvenanceRecord]:
        raise NotImplementedError()

    @abstractmethod
    def query_by_id(self, id_: str) -> ProvenanceRecord:
        raise NotImplementedError()

    @abstractmethod
    def query_by_long_name(self, long_name: str) -> ProvenanceRecord:
        raise NotImplementedError()

    @abstractmethod
    def query_by_abbreviation(self, abbreviation: str) -> ProvenanceRecord:
        raise NotImplementedError()

    @abstractmethod
    def update(self, provenance: ProvenanceRecord) -> None:
        raise NotImplementedError()

    @abstractmethod
    def find_children(self, parent_id: str) -> Sequence[ProvenanceRecord]:
        raise NotImplementedError()

    @abstractmethod
    def find_by_coordinates(
        self, latitude: float, longitude: float, radius_km: float
    ) -> Sequence[ProvenanceRecord]:
        raise NotImplementedError()
