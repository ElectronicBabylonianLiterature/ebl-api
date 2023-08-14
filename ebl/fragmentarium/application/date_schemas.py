from ebl.fragmentarium.domain.date import DateRange, DateWithNotes
from marshmallow import Schema, fields, post_load


class DateRangeSchema(Schema):
    start = fields.Date()
    end = fields.Date()
    notes = fields.String()

    @post_load
    def create_date_range(self, data, **kwargs) -> DateRange:
        return DateRange(**data)


class DateWithNotesSchema(Schema):
    date = fields.Date()
    notes = fields.String()

    @post_load
    def create_date(self, data, **kwargs) -> DateWithNotes:
        return DateWithNotes(**data)
