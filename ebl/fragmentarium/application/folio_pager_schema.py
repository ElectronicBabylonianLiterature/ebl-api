from marshmallow import Schema, fields


class FragmentNumberInfo(Schema):
    fragmentNumber: fields.String(required=True)


class FragmentPagerFolioInfo(Schema):
    previous: fields.NestedDict(FragmentNumberInfo, key="fragmentNumber")
    next: fields.NestedDict(FragmentNumberInfo, key="fragmentNumber")
