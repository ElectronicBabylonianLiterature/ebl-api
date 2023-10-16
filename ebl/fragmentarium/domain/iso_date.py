import attr
import datetime


@attr.s(auto_attribs=True, frozen=True)
class DateRange:
    start: datetime.date
    end: datetime.date
    notes: str = ""


@attr.s(auto_attribs=True, frozen=True)
class DateWithNotes:
    date: datetime.date
    notes: str = ""
