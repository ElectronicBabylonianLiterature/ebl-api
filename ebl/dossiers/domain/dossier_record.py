import attr
from typing import Sequence, Optional

from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.domain.fragment import Script
from ebl.bibliography.domain.reference import ReferenceType


@attr.s(frozen=True, auto_attribs=True)
class DossierRecord:
    id: str
    description: Optional[str] = None
    is_approximate_date: bool = False
    year_range_from: Optional[int] = None
    year_range_to: Optional[int] = None
    related_kings: Sequence[float] = []
    provenance: Optional[Provenance] = None
    script: Optional[Script] = None
    references: Sequence[ReferenceType] = []
