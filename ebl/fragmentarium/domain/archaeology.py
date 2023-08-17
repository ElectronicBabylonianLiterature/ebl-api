from typing import Optional, Sequence
import attr
from ebl.fragmentarium.domain.date import DateWithNotes
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.transliteration.domain.museum_number import MuseumNumber as ExcavationNumber
from ebl.corpus.domain.provenance import Provenance as ExcavationSite


@attr.s(auto_attribs=True, frozen=True)
class Archaeology:
    excavation_number: ExcavationNumber
    site: ExcavationSite
    regular_excavation: bool = True
    excavation_date: Optional[Sequence[DateWithNotes]] = None
    findspot: Optional[Findspot] = None
