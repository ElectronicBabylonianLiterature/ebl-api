from typing import Optional
import attr


@attr.s(auto_attribs=True, frozen=True)
class PartialDate:
    year: int
    month: Optional[int] = None
    day: Optional[int] = None


@attr.s(auto_attribs=True, frozen=True)
class DateRange:
    start: PartialDate
    end: Optional[PartialDate] = None
    notes: str = ""


@attr.s(auto_attribs=True, frozen=True)
class CommentedDate:
    date: PartialDate
    notes: str = ""
