import datetime
from ebl.fragmentarium.domain.date_range import DateRange, DateWithNotes
from marshmallow import Schema, fields, post_load
from dateutil.parser import isoparse


class IsoDateField(fields.Field):
    def _serialize(self, date: datetime.date, *args, **kwargs) -> str:
        return str(date)

    def _deserialize(self, date_string: str, *args, **kwargs) -> datetime.date:
        return isoparse(date_string).date()


class DateRangeSchema(Schema):
    start = fields.Integer()
    end = fields.Integer()
    notes = fields.String()

    @post_load
    def create_date_range(self, data, **kwargs) -> DateRange:
        return DateRange(**data)


class DateWithNotesSchema(Schema):
    date = IsoDateField()
    notes = fields.String()

    @post_load
    def create_date(self, data, **kwargs) -> DateWithNotes:
        return DateWithNotes(**data)
