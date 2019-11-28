from marshmallow import Schema, fields


class FragmentNumberInfo(Schema):
    fragmentNumber: fields.String(required=True)


class FolioPagerInfo(Schema):
    previous: fields.Nested(FragmentNumberInfo, key="fragmentNumber")
    next: fields.Nested(FragmentNumberInfo, key="fragmentNumber")
