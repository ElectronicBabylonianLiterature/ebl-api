from marshmallow import Schema, fields, post_load  # pyre-ignore[21]
from ebl.fragmentarium.domain.fragment import Genre


class GenreSchema(Schema):  # pyre-ignore[11]
    category = fields.List(fields.String, required=True)
    uncertain = fields.Boolean(required=True)

    @post_load  # pyre-ignore[56]
    def make_genre(self, data, **kwargs) -> Genre:
        return Genre(**data)
