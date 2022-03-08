from marshmallow import Schema, fields, post_load

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.domain.chapter_display import ChapterDisplay, LineDisplay
from ebl.corpus.domain.record import Record
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema


class LineDisplaySchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    intertext = fields.List(
        fields.Nested(OneOfNoteLinePartSchema), load_default=tuple(), allow_none=True
    )
    reconstruction = fields.List(fields.Nested(OneOfTokenSchema), load_default=tuple())
    translation = fields.List(
        fields.Nested(TranslationLineSchema), load_default=tuple(), allow_none=True
    )
    note = fields.Nested(NoteLineSchema, allow_none=True, load_default=None)

    @post_load
    def make_line(self, data: dict, **kwargs) -> LineDisplay:
        return LineDisplay(
            data["number"],
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["intertext"] or []),
            tuple(data["reconstruction"]),
            tuple(data["translation"] or []),
            data["note"],
        )


class ChapterDisplaySchema(Schema):
    id_ = fields.Nested(ChapterIdSchema, required=True, data_key="id")
    text_name = fields.String(required=True, data_key="textName")
    is_single_stage = fields.Boolean(required=True, data_key="isSingleStage")
    title = fields.List(fields.Nested(OneOfNoteLinePartSchema), dump_only=True)
    lines = fields.Nested(LineDisplaySchema, many=True, required=True)
    record = fields.Nested(RecordSchema, load_default=Record())

    @post_load
    def make_chapter(self, data: dict, **kwargs) -> ChapterDisplay:
        return ChapterDisplay(
            data["id_"],
            data["text_name"],
            data["is_single_stage"],
            tuple(data["lines"]),
            data["record"],
        )
