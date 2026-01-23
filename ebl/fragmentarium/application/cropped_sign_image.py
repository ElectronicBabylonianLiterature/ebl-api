import uuid
from typing import NewType

import attr
from marshmallow import Schema, fields, post_load, post_dump

from ebl.transliteration.domain.museum_number import MuseumNumber

Base64 = NewType("Base64", str)


@attr.s(auto_attribs=True, frozen=True)
class CroppedSignImage:
    image_id: str
    image: Base64
    fragment_number: MuseumNumber

    # NEW (all optional)
    sign: str | None = None
    period: str | None = None
    form: str | None = None
    is_centroid: bool | None = None
    cluster_size: int | None = None
    is_main: bool | None = None


    @classmethod
    def create(cls, image: Base64, fragment_number: MuseumNumber) -> "CroppedSignImage":
        return cls(str(uuid.uuid4()), image, fragment_number)


class CroppedSignImageSchema(Schema):
    image_id = fields.Str(required=True)
    image = fields.Str(required=True)
    fragment_number = fields.Str(required=True)

    # NEW
    sign = fields.Str(required=False, allow_none=True)
    period = fields.Str(required=False, allow_none=True)
    form = fields.Str(required=False, allow_none=True)
    isCentroid = fields.Boolean(required=False, allow_none=True)
    clusterSize = fields.Integer(required=False, allow_none=True)
    isMain = fields.Boolean(required=False, allow_none=True)


    @post_load
    def load(self, data, **kwargs):
        return CroppedSignImage(
            data["_id"],
            data["image"],
            MuseumNumber.of(data["fragment_number"]),
            data.get("sign"),
            data.get("period"),
            data.get("form"),
            data.get("isCentroid"),
            data.get("clusterSize"),
            data.get("isMain"),
            )


    @post_dump
    def cropped_sign_image_dump(self, data, **kwargs):
        result = {
            "_id": data["image_id"],
            "image": data["image"],
            "fragment_number": str(data["fragment_number"]),
            }

        # include clustering metadata only if present
        for key in [
            "sign",
            "period",
            "form",
            "is_centroid",
            "cluster_size",
            "is_main",
            ]:
            value = getattr(data, key)
            if value is not None:
                result_key = {
                    "is_centroid": "isCentroid",
                    "cluster_size": "clusterSize",
                    "is_main": "isMain",
                    }.get(key, key)
                result[result_key] = value
                
        return result



@attr.attrs(auto_attribs=True, frozen=True)
class CroppedSign:
    image_id: str
    label: str


class CroppedSignSchema(Schema):
    image_id = fields.String(required=True, data_key="imageId")
    label = fields.String(required=True)

    @post_load
    def load(self, data, **kwargs):
        return CroppedSign(data["imageId"], data["label"])
