from marshmallow import Schema, fields, post_load, validate

from ebl.corpus.domain.chapter import ChapterId
from ebl.transliteration.domain.text_id import TextId
from ebl.schemas import StageField, ValueEnumField
from ebl.transliteration.domain.genre import Genre


class TextIdSchema(Schema):
    genre = ValueEnumField(Genre, load_default=Genre.LITERATURE)
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))

    @post_load
    def make_id(self, data, **kwargs) -> TextId:
        return TextId(data["genre"], data["category"], data["index"])


class ChapterIdSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    stage = StageField(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))

    @post_load
    def make_id(self, data, **kwargs) -> ChapterId:
        return ChapterId(data["text_id"], data["stage"], data["name"])
