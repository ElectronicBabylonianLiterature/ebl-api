import falcon
from marshmallow import fields, Schema

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.web.text_utils import create_chapter_id
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema


class ExtantLineSchema(Schema):
    line_number = fields.Nested(OneOfLineNumberSchema, data_key="lineNumber")
    is_side_boundary = fields.Boolean(data_key="isSideBoundary")


class Labels(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs) -> str:
        return " ".join(label.to_value() for label in value)


class ExtantLinesSchema(Schema):
    extant_lines = fields.Dict(
        fields.String(),
        fields.Dict(Labels(), fields.Nested(ExtantLineSchema, many=True)),
        data_key="extantLines",
    )


class ExtantLinesResource:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus

    def on_get(
        self,
        _,
        resp: falcon.Response,
        genre: str,
        category: str,
        index: str,
        stage: str,
        name: str,
    ) -> None:
        chapter_id = create_chapter_id(genre, category, index, stage, name)
        chapter = self._corpus.find_chapter(chapter_id)
        resp.media = ExtantLinesSchema().dump(chapter)["extantLines"]
