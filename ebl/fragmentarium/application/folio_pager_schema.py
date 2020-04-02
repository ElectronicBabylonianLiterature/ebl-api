from marshmallow import Schema, fields  # pyre-ignore


class FragmentNumberSchema(Schema):  # pyre-ignore[11]
    fragmentNumber = fields.String()
    folioNumber = fields.String()


class FolioPagerInfoSchema(Schema):  # pyre-ignore[11]
    previous = fields.Nested(FragmentNumberSchema, required=True)
    next = fields.Nested(FragmentNumberSchema, required=True)
