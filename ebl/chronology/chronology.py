import attr
import json
from typing import Sequence, Optional
from marshmallow import Schema, fields, post_load, post_dump


@attr.s(auto_attribs=True, frozen=True)
class King:
    order_global: int
    group_with: int
    dynasty_number: str
    dynasty_name: str
    order_in_dynasty: str
    name: str
    date: str
    total_of_years: str
    notes: str
    is_not_in_brinkman: Optional[bool]


@attr.s(auto_attribs=True, frozen=True)
class Chronology:
    kings: Sequence[King] = attr.ib(factory=list)

    def find_king_by_name(self, king_name: str) -> Optional[King]:
        try:
            return [king for king in self.kings if king.name == king_name][0]
        except IndexError:
            return None


class KingSchema(Schema):
    order_global = fields.Integer(data_key="orderGlobal")
    group_with = fields.Integer(
        data_key="groupWith", allow_none=True, load_default=None
    )
    dynasty_number = fields.String(data_key="dynastyNumber")
    dynasty_name = fields.String(data_key="dynastyName")
    order_in_dynasty = fields.String(data_key="orderInDynasty")
    name = fields.String()
    date = fields.String()
    total_of_years = fields.String(data_key="totalOfYears")
    notes = fields.String(allow_none=True, load_default=None)
    is_not_in_brinkman = fields.Boolean(
        allow_none=True, load_default=None, data_key="isNotInBrinkman"
    )

    @post_load
    def make_king(self, data: dict, **kwargs) -> King:
        return King(**data)

    @post_dump
    def remove_skip_values(self, data: dict, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


@attr.s(auto_attribs=True, frozen=True)
class Eponym:
    date: str
    name: str
    title: str
    area: str
    event: str
    phase: str
    notes: str
    king: str
    isKing: bool
    rel: int


class EponymSchema(Schema):
    date = fields.String(allow_none=True, load_default=None)
    name = fields.String(allow_none=True, load_default=None)
    title = fields.String(allow_none=True, load_default=None)
    area = fields.String(allow_none=True, load_default=None)
    event = fields.String(allow_none=True, load_default=None)
    phase = fields.String()
    notes = fields.String(allow_none=True, load_default=None)
    king = fields.String(allow_none=True, load_default=None)
    isKing = fields.Boolean(allow_none=True, load_default=None)
    rel = fields.Integer(allow_none=True, load_default=None)

    @post_load
    def make_eponym(self, data: dict, **kwargs) -> Eponym:
        return Eponym(**data)

    @post_dump
    def remove_skip_values(self, data: dict, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class ChronologySchema(Schema):
    kings = fields.List(fields.Nested(KingSchema))

    @post_load
    def make_chronology(self, data: dict, **kwargs) -> Chronology:
        return Chronology(**data)


with open("ebl/chronology/brinkmanKings.json", "r", encoding="utf-8") as file:
    data = json.load(file)
    chronology = ChronologySchema().load({"kings": data})
