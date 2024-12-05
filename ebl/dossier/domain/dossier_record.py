import attr
from typing import Sequence, Optional, FrozenSet

from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.domain.fragment import Script
from ebl.bibliography.domain.reference import ReferenceType


@attr.s(frozen=True, auto_attribs=True)
class DossierRecord:
    name: str
    description: Optional[str] = None
    is_approximate_date: bool = False
    year_range_from: Optional[int] = None
    year_range_to: Optional[int] = None
    related_kings: Optional[Sequence[float]] = []
    provenance: Optional[Provenance] = None
    script: Optional[Script] = None
    references: FrozenSet[ReferenceType] = frozenset()
