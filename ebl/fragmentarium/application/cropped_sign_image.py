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

    @classmethod
    def create(cls, image: Base64) -> "CroppedSignImage":
        return cls(str(uuid.uuid4()), image)


class CroppedSignImageSchema(Schema):
    image_id = fields.Str(required=True)
    image = fields.Str(required=True)

    @post_load
    def load(self, data, **kwargs):
        return CroppedSignImage(data["_id"], data["image"])

    @post_dump
    def cropped_sign_image_dump(self, data, **kwargs):
        return {"_id": data["image_id"], "image": data["image"]}


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedSign:
    image_id: str
    script: str
    label: str


class CroppedSignSchema(Schema):
    image_id = fields.String(required=True, data_key="imageId")
    script = fields.String()
    label = fields.String(required=True)

    @post_load
    def load(self, data, **kwargs):
        return CroppedSign(data["imageId"], data.get("script", ""), data["label"])


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedAnnotation(CroppedSign):
    fragment_number: MuseumNumber
    image: Base64

    @classmethod
    def from_cropped_sign(
        cls, fragment_number: MuseumNumber, image: Base64, cropped_sign: CroppedSign
    ) -> "CroppedAnnotation":
        return cls(
            cropped_sign.image_id,
            cropped_sign.script,
            cropped_sign.label,
            fragment_number,
            image,
        )


class CroppedAnnotationSchema(CroppedSignSchema):
    fragment_number = fields.String(required=True, data_key="fragmentNumber")
    image = fields.String(required=True)
