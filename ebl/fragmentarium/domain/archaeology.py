from typing import Optional
import attr
from ebl.fragmentarium.domain.date_range import DateRange
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.transliteration.domain.museum_number import MuseumNumber as ExcavationNumber
from ebl.corpus.domain.manuscript import Provenance as ExcavationSite


@attr.s(auto_attribs=True, frozen=True)
class Archaeology:
    excavation_number: ExcavationNumber
    site: ExcavationSite
    regular_excavation: bool = True
    excavation_date: Optional[DateRange] = None
    findspot: Optional[Findspot] = None
