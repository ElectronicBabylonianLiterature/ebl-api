from marshmallow import Schema, fields, post_load

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.application.schemas import LineVariantSchema, ManuscriptSchema
from ebl.corpus.domain.chapter_display import ChapterDisplay, LineDisplay
from ebl.corpus.domain.record import Record
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    TranslationLineSchema,
)
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)


class LineDisplaySchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    variants = fields.Nested(LineVariantSchema, many=True, required=True)
    translation = fields.List(
        fields.Nested(TranslationLineSchema), load_default=tuple(), allow_none=True
    )

    @post_load
    def make_line(self, data: dict, **kwargs) -> LineDisplay:
        return LineDisplay(
            data["number"],
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["variants"]),
            tuple(data["translation"] or []),
        )


class ChapterDisplaySchema(Schema):
    id_ = fields.Nested(ChapterIdSchema, required=True, data_key="id")
    text_name = fields.String(required=True, data_key="textName")
    text_has_doi = fields.Boolean(data_key="textHasDoi", load_default=False)
    is_single_stage = fields.Boolean(required=True, data_key="isSingleStage")
    title = fields.List(fields.Nested(OneOfNoteLinePartSchema), dump_only=True)
    lines = fields.Nested(LineDisplaySchema, many=True, required=True)
    record = fields.Nested(RecordSchema, load_default=Record())
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    atf = fields.String(dump_only=True)

    @post_load
    def make_chapter(self, data: dict, **kwargs) -> ChapterDisplay:
        return ChapterDisplay(
            data["id_"],
            data["text_name"],
            data["text_has_doi"],
            data["is_single_stage"],
            tuple(data["lines"]),
            data["record"],
            tuple(data["manuscripts"]),
        )
