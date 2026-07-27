import attr
from typing import Optional, Sequence, TypeAlias
from enum import Enum, auto
from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.date_range import DateRange
from ebl.fragmentarium.domain.map_location import MapLocation
from ebl.provenance.domain.provenance_model import ProvenanceRecord


ExcavationSite: TypeAlias = ProvenanceRecord


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
    sector: str = ""
    area: str = ""
    building: str = ""
    building_type: Optional[BuildingType] = None
    lavel_layer_phase: str = ""
    date_range: Optional[DateRange] = None
    plans: Sequence[ExcavationPlan] = ()
    room: str = ""
    context: str = ""
    map_location: Optional[MapLocation] = None
    primary_context: Optional[bool] = None
    notes: str = ""
