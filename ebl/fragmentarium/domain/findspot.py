import attr
from typing import Optional, Sequence
from enum import Enum, auto
from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.date_range import DateRange
from ebl.common.domain.provenance import Provenance


ExcavationSite = Provenance


class BuildingType(Enum):
    RESIDENTIAL = auto()
    TEMPLE = auto()
    PALACE = auto()
    OTHER_MONUMENTAL = auto()
    UNKNOWN = auto()
    NOT_IN_BUILDING = auto()


@attr.s(auto_attribs=True, frozen=True)
class ExcavationPlan:
    svg: str
    references: Sequence[Reference] = ()


@attr.s(auto_attribs=True, frozen=True)
class Findspot:
    id_: int
    site: Optional[ExcavationSite] = None
    area: str = ""
    building: str = ""
    building_type: Optional[BuildingType] = None
    lavel_layer_phase: str = ""
    date_range: Optional[DateRange] = None
    plans: Sequence[ExcavationPlan] = ()
    room: str = ""
    context: str = ""
    primary_context: Optional[bool] = None
    notes: str = ""
