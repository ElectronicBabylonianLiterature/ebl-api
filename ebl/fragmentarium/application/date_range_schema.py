from marshmallow import Schema, fields


class DateRangeSchema(Schema):
    start = fields.Date()
    end = fields.Date()
    notes = fields.String()
