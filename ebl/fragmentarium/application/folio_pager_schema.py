from marshmallow import Schema, fields  # pyre-ignore[21]


class FragmentNumberSchema(Schema):  # pyre-ignore[11]
    fragmentNumber = fields.String()
    folioNumber = fields.String()


class FolioPagerInfoSchema(Schema):
    previous = fields.Nested(FragmentNumberSchema, required=True)
    next = fields.Nested(FragmentNumberSchema, required=True)
