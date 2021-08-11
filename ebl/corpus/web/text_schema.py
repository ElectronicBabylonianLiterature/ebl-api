from marshmallow import fields
import pydash

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import ChapterListingSchema, TextSchema
from ebl.transliteration.domain.translation_line import DEFAULT_LANGUAGE
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)


class ApiChapterListingSchema(ChapterListingSchema):
    title = fields.Function(
        lambda chapter: OneOfNoteLinePartSchema().dump(
            pydash.chain(chapter.translation)
            .filter(lambda line: line.language == DEFAULT_LANGUAGE)
            .map(lambda line: line.parts)
            .head()
            .value()
            or tuple(),
            many=True,
        )
    )


class ApiTextSchema(TextSchema):
    references = fields.Nested(ApiReferenceSchema, many=True)
    chapters = fields.Nested(
        ApiChapterListingSchema, exclude=["translation"], many=True, required=True
    )
