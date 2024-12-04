import attr
from typing import Sequence, Optional

from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.domain.fragment import Script
from ebl.bibliography.domain.reference import ReferenceType


@attr.s(frozen=True, auto_attribs=True)
class AfoRegisterRecord:
    id: int
    name: str
    description: str
    is_approximate_date: bool
    year_range_from: Optional[int] = None
    year_range_to: Optional[int] = None
    related_kings: Sequence[int]
    provenance: Provenance
    script: Script
    references: Sequence[ReferenceType]
