from marshmallow import Schema, fields


class FolioPagerInfoSchema(Schema):
    previous = fields.String(required=True)
    next = fields.String(required=True)
