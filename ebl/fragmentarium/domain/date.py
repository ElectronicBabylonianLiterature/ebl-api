import attr
import pydash
from typing import Optional, Set
from marshmallow import Schema, fields, post_load, post_dump, EXCLUDE
from enum import Enum
from ebl.schemas import ValueEnumField
from ebl.chronology.chronology import chronology, King, Eponym, EponymSchema

WRAPPERS = {
    "<": (">", "is_reconstructed"),
    "[": ("]", "is_broken"),
    "(": (")", "is_uncertain"),
}
TRAILING_MARKERS = {"!": "is_emended", "?": "is_uncertain"}


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
    is_reconstructed: Optional[bool] = attr.ib(default=None)
    is_emended: Optional[bool] = attr.ib(default=None)
    original_value: Optional[str] = attr.ib(default=None)


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
class DateKing:
    order_global: float
    is_broken: Optional[bool] = attr.ib(default=None)
    is_uncertain: Optional[bool] = attr.ib(default=None)

    @property
    def king(self) -> Optional[King]:
        return chronology.find_king_by_order_global(self.order_global)


@attr.s(auto_attribs=True)
class DateEponym(Eponym):
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


def _caller_set_flags(data: dict) -> Set[str]:
    flag_keys = {key for _, key in WRAPPERS.values()} | set(TRAILING_MARKERS.values())
    return {key for key in flag_keys if data.get(key) is not None}


def _strip_trailing_marker(
    value: str, data: dict, caller_set: Set[str]
) -> Optional[str]:
    if len(value) <= 1 or value[-1] not in TRAILING_MARKERS:
        return None
    key = TRAILING_MARKERS[value[-1]]
    if key in caller_set:
        return None
    data[key] = True
    return value[:-1]


def _strip_wrapper(value: str, data: dict, caller_set: Set[str]) -> Optional[str]:
    if len(value) <= 2 or value[0] not in WRAPPERS:
        return None
    end, key = WRAPPERS[value[0]]
    if not value.endswith(end) or key in caller_set:
        return None
    data[key] = True
    return value[1:-1]


def _peel_year_value(value: str, data: dict, caller_set: Set[str]) -> str:
    while value:
        stripped = _strip_trailing_marker(value, data, caller_set)
        if stripped is None:
            stripped = _strip_wrapper(value, data, caller_set)
        if stripped is None:
            return value
        value = stripped
    return value


def _parse_year_value(data: dict) -> dict:
    data = dict(data)
    raw_value = data.get("value", "")
    value = _peel_year_value(raw_value, data, _caller_set_flags(data))
    data["value"] = value
    if value != raw_value and "original_value" not in data:
        data["original_value"] = raw_value
    return data


class YearSchema(LabeledSchema):
    is_reconstructed = fields.Boolean(data_key="isReconstructed", allow_none=True)
    is_emended = fields.Boolean(data_key="isEmended", allow_none=True)
    original_value = fields.String(data_key="originalValue", allow_none=True)

    @post_load
    def make_year(self, data, **kwargs) -> Year:
        return Year(**_parse_year_value(data))


class MonthSchema(LabeledSchema):
    is_intercalary = fields.Boolean(data_key="isIntercalary", allow_none=True)

    @post_load
    def make_month(self, data, **kwargs) -> Month:
        return Month(**data)


class DaySchema(LabeledSchema):
    @post_load
    def make_day(self, data, **kwargs) -> Day:
        return Day(**data)


class DateKingSchema(Schema):
    order_global = fields.Float(data_key="orderGlobal")
    is_broken = fields.Boolean(data_key="isBroken", allow_none=True)
    is_uncertain = fields.Boolean(data_key="isUncertain", allow_none=True)

    @post_load
    def make_date_king(self, data: dict, **kwargs) -> DateKing:
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
