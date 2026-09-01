from typing import Optional, Protocol, Sequence, runtime_checkable

from ebl.provenance.domain.provenance_model import ProvenanceRecord


@runtime_checkable
class ProvenanceLookup(Protocol):
    def find_by_name(self, name: str) -> Optional[ProvenanceRecord]: ...

    def find_by_id(self, id_: str) -> Optional[ProvenanceRecord]: ...

    def find_children(self, parent: str) -> Sequence[ProvenanceRecord]: ...
