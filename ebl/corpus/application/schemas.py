from typing import Any

from marshmallow import Schema, fields, post_load, validate

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.application.id_schemas import TextIdSchema, ChapterIdSchema
from ebl.corpus.application.line_schemas import (
    DictionaryLinePaginationSchema as DictionaryLinePaginationSchema,
    DictionaryLineSchema as DictionaryLineSchema,
    LineSchema as LineSchema,
    LineVariantSchema as LineVariantSchema,
    ManuscriptLineSchema as ManuscriptLineSchema,
    manuscript_id as manuscript_id,
)
from ebl.corpus.application.manuscript_schemas import (
    ManuscriptSchema as ManuscriptSchema,
    OldSiglumSchema as OldSiglumSchema,
)
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.chapter_query import ChapterQueryColophonLinesSchema
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.record import Record
from ebl.corpus.domain.text import ChapterListing, Text, UncertainFragment
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)
from ebl.schemas import ResearchProjectField, StageField, ValueEnumField
from ebl.transliteration.application.label_schemas import labels as labels
from ebl.transliteration.application.line_schemas import TranslationLineSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.genre import Genre


__all__ = [
    "ChapterListingSchema",
    "ChapterSchema",
    "ManuscriptAttestationSchema",
    "TextSchema",
    "UncertainFragmentAttestationSchema",
    "UncertainFragmentSchema",
    "DictionaryLinePaginationSchema",
    "DictionaryLineSchema",
    "LineSchema",
    "LineVariantSchema",
    "ManuscriptLineSchema",
    "ManuscriptSchema",
    "OldSiglumSchema",
    "labels",
    "manuscript_id",
]


class ChapterSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    classification = ValueEnumField(Classification, required=True)
    stage = StageField(required=True)
    version = fields.String(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    text_name = fields.String(data_key="textName", load_only=True, load_default="")
    order = fields.Integer(required=True)
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    uncertain_fragments: fields.Field = fields.Nested(
        MuseumNumberSchema,
        many=True,
        load_default=(),
        data_key="uncertainFragments",
    )
    lines = fields.Nested(LineSchema, many=True, required=True)
    signs = fields.List(fields.String(allow_none=True), load_default=())
    record = fields.Nested(RecordSchema, load_default=Record())
    parser_version = fields.String(load_default="", data_key="parserVersion")
    is_filtered_query = fields.Bool(load_default=False, data_key="isFilteredQuery")
    colophon_lines_in_query = fields.Nested(
        ChapterQueryColophonLinesSchema,
        load_default={"colophonLinesInQuery": {}},
        data_key="colophonLinesInQuery",
    )

    @post_load
    def make_chapter(self, data: dict[str, Any], **kwargs: object) -> Chapter:
        return Chapter(
            data["text_id"],
            Classification(data["classification"]),
            data["stage"],
            data["version"],
            data["name"],
            data["order"],
            tuple(data["manuscripts"]),
            tuple(data["uncertain_fragments"]),
            tuple(data["lines"]),
            tuple(data["signs"]),
            data["record"],
            data["parser_version"],
            data["is_filtered_query"],
            data["colophon_lines_in_query"],
            data["text_name"],
        )


class UncertainFragmentSchema(Schema):
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )

    @post_load
    def make_uncertain_fragment(
        self, data: dict[str, Any], **kwargs: object
    ) -> UncertainFragment:
        return UncertainFragment(data["museum_number"])


class ChapterListingSchema(Schema):
    stage = StageField(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    translation = fields.Nested(TranslationLineSchema, many=True, load_default=())
    uncertain_fragments = fields.Nested(
        UncertainFragmentSchema,
        many=True,
        load_default=(),
        data_key="uncertainFragments",
    )

    @post_load
    def make_chapter_listing(
        self, data: dict[str, Any], **kwargs: object
    ) -> ChapterListing:
        return ChapterListing(
            data["stage"],
            data["name"],
            tuple(data["translation"]),
            tuple(data["uncertain_fragments"]),
        )


class TextSchema(Schema):
    genre = ValueEnumField(Genre, load_default=Genre.LITERATURE)
    category = fields.Integer(required=True, validate=validate.Range(min=0))
    index = fields.Integer(required=True, validate=validate.Range(min=0))
    name = fields.String(required=True, validate=validate.Length(min=1))
    has_doi = fields.Boolean(load_default=False, data_key="hasDoi")
    number_of_verses = fields.Integer(
        required=True, data_key="numberOfVerses", validate=validate.Range(min=0)
    )
    approximate_verses = fields.Boolean(required=True, data_key="approximateVerses")
    intro = fields.String(load_default="")
    chapters = fields.Nested(ChapterListingSchema, many=True, required=True)
    references = fields.Nested(ReferenceSchema, many=True, load_default=())
    projects = fields.List(ResearchProjectField(), load_default=())

    @post_load
    def make_text(self, data: dict[str, Any], **kwargs: object) -> Text:
        return Text(
            data["genre"],
            data["category"],
            data["index"],
            data["name"],
            data["has_doi"],
            data["number_of_verses"],
            data["approximate_verses"],
            data["intro"],
            tuple(data["chapters"]),
            tuple(data["references"]),
            tuple(data["projects"]),
        )


class ManuscriptAttestationSchema(Schema):
    text = fields.Nested(TextSchema, required=True)
    chapter_id = fields.Nested(ChapterIdSchema, data_key="chapterId", required=True)
    manuscript = fields.Nested(ManuscriptSchema, required=True)
    manuscript_siglum = fields.String(
        load_default="",
        data_key="manuscriptSiglum",
    )

    @post_load
    def make_manuscript_attestation(
        self, data: dict[str, Any], **kwargs: object
    ) -> ManuscriptAttestation:
        return ManuscriptAttestation(
            data["text"],
            data["chapter_id"],
            data["manuscript"],
        )


class UncertainFragmentAttestationSchema(Schema):
    text = fields.Nested(TextSchema, required=True)
    chapter_id = fields.Nested(ChapterIdSchema, data_key="chapterId", required=True)

    @post_load
    def make_uncertain_fragment_attestation(
        self, data: dict[str, Any], **kwargs: object
    ) -> UncertainFragmentAttestation:
        return UncertainFragmentAttestation(data["text"], data["chapter_id"])
