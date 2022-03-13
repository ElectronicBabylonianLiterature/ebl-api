from typing import NewType

import attr

Base64 = NewType("Base64", str)


@attr.s(auto_attribs=True, frozen=True)
class CroppedSignImage:
    image_id: str
    image: Base64




class CroppedSignImageSchema(Schema):
    image = fields.Str(required=True)

    @post_load
    def load(self, data, **kwargs):
        return CroppedSignImage(data["_id"], data["image"])

    @post_dump
    def dump(self, data, **kwargs):
        return {"_id": data["image_id"], "image": data["image"]}
