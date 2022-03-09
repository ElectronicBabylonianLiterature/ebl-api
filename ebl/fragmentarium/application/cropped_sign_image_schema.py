from marshmallow import Schema, fields, post_dump

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage


class CroppedSignImageSchema(Schema):
    class Meta:
        model = CroppedSignImage

    sign_id = fields.Str(required=True)
    image = fields.Str(required=True)

    @post_dump
    def dump(self, data, **kwargs):
        return CroppedSignImage(**data)
