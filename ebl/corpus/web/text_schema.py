from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import ChapterListingSchema, TextSchema
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)


class ApiChapterListingSchema(ChapterListingSchema):
    title = fields.Nested(OneOfNoteLinePartSchema, many=True)


class ApiTextSchema(TextSchema):
    references = fields.Nested(ApiReferenceSchema, many=True)
    chapters = fields.Nested(
        ApiChapterListingSchema, exclude=["translation"], many=True, required=True
    )
