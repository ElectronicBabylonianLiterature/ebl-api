from marshmallow import Schema, fields, post_load, validate  # pyre-ignore[21]

from ebl.fragmentarium.domain.museum_number import MuseumNumber


class MuseumNumberSchema(Schema):  # pyre-ignore[11]
    prefix = fields.String(required=True, validate=validate.Length(min=1))
    number = fields.String(
        required=True, validate=(validate.Length(min=1), validate.ContainsNoneOf("."))
    )
    suffix = fields.String(required=True, validate=validate.ContainsNoneOf("."))

    @post_load
    def create_museum_number(self, data, **kwargs) -> MuseumNumber:
        return MuseumNumber(**data)
