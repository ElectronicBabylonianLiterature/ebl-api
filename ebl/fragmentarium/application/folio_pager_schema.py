from marshmallow import Schema, fields


class FragmentNumberSchema(Schema):
    fragmentNumber = fields.String()
    folioNumber = fields.String()


class FolioPagerInfoSchema(Schema):
    previous = fields.Nested(FragmentNumberSchema, required=True)
    next = fields.Nested(FragmentNumberSchema, required=True)
