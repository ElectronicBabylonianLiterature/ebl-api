from marshmallow import Schema, fields


class FragmentPagerInfo(Schema):
    previous = fields.String(required=True)
    next = fields.String(required=True)
