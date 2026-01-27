import uuid
from typing import NewType, Optional


import attr
from marshmallow import Schema, fields, post_load, post_dump

from ebl.transliteration.domain.museum_number import MuseumNumber

Base64 = NewType("Base64", str)


@attr.s(auto_attribs=True, frozen=True)
class CroppedSignImage:
    image_id: str
    image: Base64
    fragment_number: MuseumNumber

    sign: Optional[str] = None
    period: Optional[str] = None
    form: Optional[str] = None
    is_centroid: Optional[bool] = None
    cluster_size: Optional[int] = None
    is_main: Optional[bool] = None

    @classmethod
    def create(cls, image: Base64, fragment_number: MuseumNumber) -> "CroppedSignImage":
        return cls(str(uuid.uuid4()), image, fragment_number)


class CroppedSignImageSchema(Schema):
    image_id = fields.Str(required=True, data_key="_id")
    image = fields.Str(required=True)
    fragment_number = fields.Str(required=True)

    sign = fields.Str(required=False, allow_none=True)
    period = fields.Str(required=False, allow_none=True)
    form = fields.Str(required=False, allow_none=True)

    is_centroid = fields.Boolean(required=False, allow_none=True, data_key="isCentroid")
    cluster_size = fields.Integer(
        required=False, allow_none=True, data_key="clusterSize"
    )
    is_main = fields.Boolean(required=False, allow_none=True, data_key="isMain")

    @post_load
    def load(self, data, **kwargs):
        return CroppedSignImage(
            image_id=data["_id"],
            image=data["image"],
            fragment_number=MuseumNumber.of(data["fragment_number"]),
            sign=data.get("sign"),
            period=data.get("period"),
            form=data.get("form"),
            is_centroid=data.get("is_centroid"),
            cluster_size=data.get("cluster_size"),
            is_main=data.get("is_main"),
        )

    @post_dump(pass_original=True)
    def cropped_sign_image_dump(self, data, original, **kwargs):
        """
        Remove optional metadata fields when they are None.
        Keeps backward compatibility with old documents.
        """
        optional_keys = [
            "sign",
            "period",
            "form",
            "isCentroid",
            "clusterSize",
            "isMain",
        ]

        return {
            k: v for k, v in data.items() if k not in optional_keys or v is not None
        }


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
