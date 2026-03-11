from marshmallow import Schema, fields, post_load

from ebl.fragmentarium.domain.fragment import Genre


class GenreSchema(Schema):
    category = fields.List(fields.String, required=True)
    uncertain = fields.Boolean(required=True)

    @post_load
    def make_genre(self, data, **kwargs) -> Genre:
        return Genre(**data)
