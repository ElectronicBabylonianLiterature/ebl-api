from typing import Optional
import attr


@attr.s(auto_attribs=True, frozen=True)
class PartialDate:
    year: int
    month: Optional[int]
    day: Optional[int]


@attr.s(auto_attribs=True, frozen=True)
class DateRange:
    start: PartialDate
    end: Optional[PartialDate]
    notes: str = ""


@attr.s(auto_attribs=True, frozen=True)
class DateWithNotes:
    date: PartialDate
    notes: str = ""
