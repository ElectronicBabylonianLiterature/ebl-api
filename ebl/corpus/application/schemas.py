from marshmallow import Schema, fields, post_load, validate

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
)
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text import ChapterListing, Text
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.schemas import ValueEnum
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.one_of_line_schema import (
    OneOfLineSchema,
    ParallelLineSchema,
)
from ebl.transliteration.application.text_schema import (
    TextSchema as TransliterationSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.application.label_schemas import labels
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.corpus.domain.text_id import TextId


class ManuscriptSchema(Schema):
    id = fields.Integer(required=True)
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    museum_number: fields.Field = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    accession = fields.String(required=True)
    period_modifier = ValueEnum(
        PeriodModifier, required=True, data_key="periodModifier"
    )
    period = fields.Function(
        lambda manuscript: manuscript.period.long_name,
        lambda value: Period.from_name(value),
        required=True,
    )
    provenance = fields.Function(
        lambda manuscript: manuscript.provenance.long_name,
        lambda value: Provenance.from_name(value),
        required=True,
    )
    type = fields.Function(
        lambda manuscript: manuscript.type.long_name,
        lambda value: ManuscriptType.from_name(value),
        required=True,
    )
    notes = fields.String(required=True)
    colophon: fields.Field = fields.Nested(
        TransliterationSchema, missing=Transliteration()
    )
    references = fields.Nested(ReferenceSchema, many=True, required=True)

    @post_load
    def make_manuscript(self, data: dict, **kwargs) -> Manuscript:
        return Manuscript(
            data["id"],
            data["siglum_disambiguator"],
            data["museum_number"],
            data["accession"],
            data["period_modifier"],
            data["period"],
            data["provenance"],
            data["type"],
            data["notes"],
            data["colophon"],
            tuple(data["references"]),
        )


def manuscript_id():
    return fields.Integer(
        required=True, data_key="manuscriptId", validate=validate.Range(min=1)
    )


class ManuscriptLineSchema(Schema):
    manuscript_id = manuscript_id()
    labels = labels()
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            data["line"],
            tuple(data["paratext"]),
            tuple(data["omitted_words"]),
        )


class LineVariantSchema(Schema):
    reconstruction: fields.Field = fields.Nested(
        OneOfTokenSchema, required=True, many=True
    )
    note = fields.Nested(NoteLineSchema, required=True, allow_none=True)
    manuscripts = fields.Nested(ManuscriptLineSchema, many=True, required=True)
    parallel_lines = fields.Nested(
        ParallelLineSchema, many=True, missing=tuple(), data_key="parallelLines"
    )

    @post_load
    def make_line_variant(self, data: dict, **kwargs) -> LineVariant:
        return LineVariant(
            tuple(data["reconstruction"]),
            data["note"],
            tuple(data["manuscripts"]),
            tuple(data["parallel_lines"]),
        )


class LineSchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    variants = fields.Nested(
        LineVariantSchema, many=True, required=True, validate=validate.Length(min=1)
    )
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    translation = fields.Nested(TranslationLineSchema, many=True, missing=tuple())

    @post_load
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["number"],
            tuple(data["variants"]),
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["translation"]),
        )


class TextIdSchema(Schema):
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))

    @post_load
    def make_text_id(self, data: dict, **kwargs) -> TextId:
        return TextId(data["category"], data["index"])


class ChapterSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    classification = ValueEnum(Classification, required=True)
    stage = ValueEnum(Stage, required=True)
    version = fields.String(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    order = fields.Integer(required=True)
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    uncertain_fragments: fields.Field = fields.Nested(
        MuseumNumberSchema, many=True, missing=tuple(), data_key="uncertainFragments"
    )
    lines = fields.Nested(LineSchema, many=True, required=True)
    signs = fields.List(fields.String(), missing=tuple())
    parser_version = fields.String(missing="", data_key="parserVersion")

    @post_load
    def make_chapter(self, data: dict, **kwargs) -> Chapter:
        return Chapter(
            data["text_id"],
            Classification(data["classification"]),
            Stage(data["stage"]),
            data["version"],
            data["name"],
            data["order"],
            tuple(data["manuscripts"]),
            tuple(data["uncertain_fragments"]),
            tuple(data["lines"]),
            tuple(data["signs"]),
            data["parser_version"],
        )


class ChapterListingSchema(Schema):
    stage = ValueEnum(Stage, required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))

    @post_load
    def make_chapter_listing(self, data: dict, **kwargs) -> ChapterListing:
        return ChapterListing(Stage(data["stage"]), data["name"])


class TextSchema(Schema):
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))
    name = fields.String(required=True, validate=validate.Length(min=1))
    number_of_verses = fields.Integer(
        required=True, data_key="numberOfVerses", validate=validate.Range(min=0)
    )
    approximate_verses = fields.Boolean(required=True, data_key="approximateVerses")
    chapters = fields.Nested(ChapterListingSchema, many=True, required=True)

    @post_load
    def make_text(self, data: dict, **kwargs) -> Text:
        return Text(
            data["category"],
            data["index"],
            data["name"],
            data["number_of_verses"],
            data["approximate_verses"],
            tuple(data["chapters"]),
        )
