from marshmallow import Schema, fields, post_load, validate

from ebl.fragmentarium.domain.museum_number import MuseumNumber


class MuseumNumberSchema(Schema):
    prefix = fields.String(required=True, validate=validate.Length(min=1))
    number = fields.String(required=True, validate=(validate.Length(min=1)))
    suffix = fields.String(required=True)

    @post_load
    def create_museum_number(self, data, **kwargs) -> MuseumNumber:
        if "." in data["number"]:
            print(data)
        data["number"] = "10000"
        return MuseumNumber(**data)
