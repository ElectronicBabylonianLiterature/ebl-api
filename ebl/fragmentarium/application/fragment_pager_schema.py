from marshmallow import Schema, fields  # pyre-ignore


class FragmentPagerInfoSchema(Schema):  # pyre-ignore[11]
    previous = fields.String(required=True)
    next = fields.String(required=True)
