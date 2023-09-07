import attr
import pydash
from typing import Optional
from marshmallow import Schema, fields, post_load, post_dump, EXCLUDE
from enum import Enum
from ebl.schemas import ValueEnumField
from ebl.chronology.chronology import King, KingSchema, Eponym, EponymSchema


class Ur3Calendar(Enum):
    NONE = None
    ADAB = "Adab"
    GIRSU = "Girsu"
    IRISAGRIG = "Irisagrig"
    NIPPUR = "Nippur"
    PUZRISHDAGAN = "Puzriš-Dagan"
    UMMA = "Umma"
    UR = "Ur"


@attr.s(auto_attribs=True, frozen=True)
class Year:
    value: str
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class Month:
    value: str
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)
    is_intercalary: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class Day:
    value: str
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class Date:
    year: Year
    month: Month
    day: Day
    king: Optional[King] = attr.ib(default=None)
    eponym: Optional[Eponym] = attr.ib(default=None)
    is_seleucid_era: Optional[bool] = attr.ib(default=None)
    is_assyrian_date: Optional[bool] = attr.ib(default=None)
    ur3_calendar: Ur3Calendar = attr.ib(default=Ur3Calendar.NONE)


class LabeledSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    value = fields.String()
    is_broken = fields.Boolean(data_key="isBroken", allow_none=True)
    is_uncertain = fields.Boolean(data_key="isUncertain", allow_none=True)

    @post_dump
    def filter_none(self, data: dict, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class YearSchema(LabeledSchema):
    @post_load
    def make_year(self, data, **kwargs) -> Year:
        return Year(**data)


class MonthSchema(LabeledSchema):
    is_intercalary = fields.Boolean(data_key="isIntercalary", allow_none=True)

    @post_load
    def make_month(self, data, **kwargs) -> Month:
        return Month(**data)


class DaySchema(LabeledSchema):
    @post_load
    def make_day(self, data, **kwargs) -> Day:
        return Day(**data)


class DateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    year = fields.Nested(YearSchema())
    month = fields.Nested(MonthSchema())
    day = fields.Nested(DaySchema())
    king = fields.Nested(KingSchema(), allow_none=True)
    eponym = fields.Nested(EponymSchema(), allow_none=True)
    is_assyrian_date = fields.Boolean(data_key="isAssyrianDate", allow_none=True)
    is_seleucid_era = fields.Boolean(data_key="isSeleucidEra", allow_none=True)
    ur3_calendar = ValueEnumField(Ur3Calendar, data_key="ur3Calendar", allow_none=True)

    @post_load
    def make_date(self, data, **kwargs) -> Date:
        return Date(**data)

    @post_dump
    def filter_none(self, data: dict, **kwargs):
        return pydash.omit_by(data, pydash.is_none)
