from marshmallow import fields, post_load, Schema, validate

from ebl.corpus.domain.text_id import TextId
from ebl.schemas import ValueEnum
from ebl.transliteration.domain.genre import Genre


class TextIdSchema(Schema):
    genre = ValueEnum(Genre, missing=Genre.LITERATURE)
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))

    @post_load
    def make_id(self, data, **kwargs) -> TextId:
        return TextId(data["genre"], data["category"], data["index"])
