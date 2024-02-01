from typing import Optional, Sequence
import attr
from ebl.fragmentarium.domain.date_range import PartialDate
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.findspot import Findspot, ExcavationSite
import re


class ExcavationNumber(MuseumNumber):
    @staticmethod
    def of(source: str) -> "ExcavationNumber":
        if match := re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?").fullmatch(source):
            return ExcavationNumber(match[1], match[2], match[3] or "")
        else:
            raise ValueError(f"'{source}' is not a valid excavation number.")


@attr.s(auto_attribs=True, frozen=True)
class Archaeology:
    excavation_number: Optional[ExcavationNumber] = None
    site: Optional[ExcavationSite] = None
    regular_excavation: bool = True
    excavation_date: Sequence[PartialDate] = tuple()
    findspot_id: Optional[int] = None
    findspot: Optional[Findspot] = None
