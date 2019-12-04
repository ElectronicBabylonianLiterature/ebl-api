from marshmallow import Schema, fields


class FolioPagerInfo(Schema):
    previous: fields.String(required=True)
    next: fields.String(required=True)
