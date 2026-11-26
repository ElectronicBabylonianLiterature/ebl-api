import datetime
from ebl.fragmentarium.domain.date_range import DateRange, PartialDate
from marshmallow import Schema, fields, post_load, post_dump
from dateutil.parser import isoparse


class IsoDateField(fields.Field):
    def _serialize(self, value: datetime.date, *args: object, **kwargs: object) -> str:
        return str(value)

    def _deserialize(
        self, value: str, *args: object, **kwargs: object
    ) -> datetime.date:
        return isoparse(value).date()


class PartialDateSchema(Schema):
    year = fields.Integer(allow_none=True)
    month = fields.Integer(allow_none=True)
    day = fields.Integer(allow_none=True)
    notes = fields.String(allow_none=True, load_default="")

    @post_load
    def create_partial_date(self, data: dict, **kwargs: object) -> PartialDate:
        return PartialDate(**data)

    @post_dump
    def remove_empty_fields(self, data: dict, **kwargs: object) -> dict:
        return {key: value for key, value in data.items() if value or value == 0}


class DateRangeSchema(Schema):
    start = fields.Nested(PartialDateSchema, allow_none=True)
    end = fields.Nested(PartialDateSchema, allow_none=True, required=False)
    notes = fields.String(allow_none=True)

    @post_load
    def create_date_range(self, data: dict, **kwargs: object) -> DateRange:
        return DateRange(**data)
