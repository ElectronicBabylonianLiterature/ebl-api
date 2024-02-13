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


@attr.s(auto_attribs=True)
class DateKing(King):
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True)
class DateEponym(Eponym):
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class DateKing(King):
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class Date:
    year: Year
    month: Month
    day: Day
    king: Optional[DateKing] = attr.ib(default=None)
    eponym: Optional[DateEponym] = attr.ib(default=None)
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


class DateKingSchema(KingSchema):
    is_broken = fields.Boolean(data_key="isBroken", allow_none=True)
    is_uncertain = fields.Boolean(data_key="isUncertain", allow_none=True)

    @post_load
    def make_king(self, data: dict, **kwargs) -> DateKing:
        return DateKing(**data)

    @post_dump
    def remove_skip_values(self, data: dict, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class DateEponymSchema(EponymSchema):
    is_broken = fields.Boolean(data_key="isBroken", allow_none=True)
    is_uncertain = fields.Boolean(data_key="isUncertain", allow_none=True)

    @post_load
    def make_eponym(self, data: dict, **kwargs) -> DateEponym:
        return DateEponym(**data)


class DateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    year = fields.Nested(YearSchema())
    month = fields.Nested(MonthSchema())
    day = fields.Nested(DaySchema())
    king = fields.Nested(DateKingSchema(), allow_none=True)
    eponym = fields.Nested(DateEponymSchema(), allow_none=True)
    is_assyrian_date = fields.Boolean(data_key="isAssyrianDate", allow_none=True)
    is_seleucid_era = fields.Boolean(data_key="isSeleucidEra", allow_none=True)
    ur3_calendar = ValueEnumField(Ur3Calendar, data_key="ur3Calendar", allow_none=True)

    @post_load
    def make_date(self, data, **kwargs) -> Date:
        return Date(**data)

    @post_dump
    def filter_none(self, data: dict, **kwargs):
        return pydash.omit_by(data, pydash.is_none)
