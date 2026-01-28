from marshmallow import Schema, fields


class FragmentPagerInfoSchema(Schema):
    previous = fields.String(required=True)
    next = fields.String(required=True)
