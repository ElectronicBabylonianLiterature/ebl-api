from marshmallow import Schema, fields, post_load, validate

from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.schemas import ValueEnum
from ebl.transliteration.domain.genre import Genre


class TextIdSchema(Schema):
    genre = ValueEnum(Genre, load_default=Genre.LITERATURE)
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))

    @post_load
    def make_id(self, data, **kwargs) -> TextId:
        return TextId(data["genre"], data["category"], data["index"])


class ChapterIdSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    stage = ValueEnum(Stage, required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))

    @post_load
    def make_id(self, data, **kwargs) -> ChapterId:
        return ChapterId(data["text_id"], data["stage"], data["name"])
