from typing import Sequence, Optional, Dict

from ebl.common.application.provenance_repository import ProvenanceRepository
from ebl.common.domain.provenance_model import ProvenanceRecord
from ebl.errors import NotFoundError


class ProvenanceService:
    def __init__(self, repository: ProvenanceRepository):
        self._repository = repository
        self._by_name_cache: Dict[str, Optional[ProvenanceRecord]] = {}
        self._by_abbreviation_cache: Dict[str, Optional[ProvenanceRecord]] = {}
        self._all_cache: Optional[Sequence[ProvenanceRecord]] = None

    def find_by_name(self, name: str) -> Optional[ProvenanceRecord]:
        if name in self._by_name_cache:
            return self._by_name_cache[name]
        try:
            record = self._repository.query_by_long_name(name)
        except NotFoundError:
            record = None
        self._by_name_cache[name] = record
        return record

    def find_by_abbreviation(self, abbreviation: str) -> Optional[ProvenanceRecord]:
        if abbreviation in self._by_abbreviation_cache:
            return self._by_abbreviation_cache[abbreviation]
        try:
            record = self._repository.query_by_abbreviation(abbreviation)
        except NotFoundError:
            record = None
        self._by_abbreviation_cache[abbreviation] = record
        return record

    def find_by_id(self, id_: str) -> Optional[ProvenanceRecord]:
        try:
            return self._repository.query_by_id(id_)
        except NotFoundError:
            return None

    def find_all(self) -> Sequence[ProvenanceRecord]:
        if self._all_cache is None:
            self._all_cache = self._repository.find_all()
        return self._all_cache

    def find_children(self, parent: str) -> Sequence[ProvenanceRecord]:
        return self._repository.find_children(parent)

    def update(self, provenance: ProvenanceRecord) -> None:
        self._repository.update(provenance)
        self._by_name_cache.clear()
        self._by_abbreviation_cache.clear()
        self._all_cache = None
