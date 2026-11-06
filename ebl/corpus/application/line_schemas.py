from typing import Any

from marshmallow import Schema, fields, post_load, validate

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.application.manuscript_schemas import ManuscriptSchema
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.schemas import StageField
from ebl.transliteration.application.label_schemas import labels
from ebl.transliteration.application.line_number_schemas import (
    OneOfLineNumberSchema,
    OldLineNumberSchema,
)
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.one_of_line_schema import (
    OneOfLineSchema,
    ParallelLineSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema


def manuscript_id() -> fields.Integer:
    return fields.Integer(
        required=True, data_key="manuscriptId", validate=validate.Range(min=1)
    )


class ManuscriptLineSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    manuscript_id = manuscript_id()
    labels = labels()
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load
    def make_manuscript_line(
        self, data: dict[str, Any], **kwargs: object
    ) -> ManuscriptLine:
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            data["line"],
            tuple(data["paratext"]),
            tuple(data["omitted_words"]),
        )


class LineVariantSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    reconstruction: fields.Field = fields.Nested(
        OneOfTokenSchema, required=True, many=True
    )
    note = fields.Nested(NoteLineSchema, required=True, allow_none=True)
    manuscripts = fields.Nested(ManuscriptLineSchema, many=True, required=True)
    parallel_lines = fields.Nested(
        ParallelLineSchema, many=True, load_default=(), data_key="parallelLines"
    )
    intertext: fields.Field = fields.Nested(
        OneOfNoteLinePartSchema, many=True, load_default=()
    )

    @post_load
    def make_line_variant(self, data: dict[str, Any], **kwargs: object) -> LineVariant:
        return LineVariant(
            tuple(data["reconstruction"]),
            data["note"],
            tuple(data["manuscripts"]),
            tuple(data["parallel_lines"]),
            tuple(data["intertext"]),
        )


class LineSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    number = fields.Nested(OneOfLineNumberSchema, required=True)
    old_line_numbers = fields.Nested(
        OldLineNumberSchema, data_key="oldLineNumbers", many=True, load_default=()
    )
    variants = fields.Nested(
        LineVariantSchema, many=True, required=True, validate=validate.Length(min=1)
    )
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    translation = fields.Nested(TranslationLineSchema, many=True, load_default=())

    @post_load
    def make_line(self, data: dict[str, Any], **kwargs: object) -> Line:
        return Line(
            data["number"],
            tuple(data["variants"]),
            tuple(data["old_line_numbers"]),
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["translation"]),
        )


class DictionaryLineSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    text_name = fields.String(required=True, data_key="textName")
    chapter_name = fields.String(
        required=True, validate=validate.Length(min=1), data_key="chapterName"
    )
    stage = StageField(required=True)
    line = fields.Nested(LineSchema, required=True)
    manuscripts: fields.Field | None = fields.Nested(
        ManuscriptSchema, required=True, many=True
    )

    @post_load
    def make_dictionary_line(
        self, data: dict[str, Any], **kwargs: object
    ) -> DictionaryLine:
        return DictionaryLine(
            data["text_id"],
            data["text_name"],
            data["chapter_name"],
            data["stage"],
            data["line"],
            tuple(data["manuscripts"]),
        )


class DictionaryLinePaginationSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    dictionary_lines = fields.Nested(
        DictionaryLineSchema,
        required=True,
        many=True,
        data_key="dictionaryLines",
    )
    total_count = fields.Integer(required=True, data_key="totalCount")
