from ebl.corpus.domain.manuscript_type import ManuscriptType
from ebl.corpus.domain.provenance import Provenance
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.domain.period import Period, PeriodModifier
from ebl.corpus.application.id_schemas import TextIdSchema, ChapterIdSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.domain.chapter import (
    Chapter,
    Classification,
)
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import (
    Manuscript,
    OldSiglum,
    is_invalid_non_standard_text,
    is_invalid_standard_text,
)
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.record import Record
from ebl.transliteration.domain.stage import Stage
from ebl.corpus.domain.text import ChapterListing, Text, UncertainFragment
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.schemas import ResearchProjectField, ValueEnumField
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
from ebl.transliteration.application.text_schema import (
    TextSchema as TransliterationSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.corpus.domain.chapter_query import ChapterQueryColophonLinesSchema


class OldSiglumSchema(Schema):
    siglum = fields.String(required=True)
    reference = fields.Nested(ReferenceSchema, required=True)

    @post_load
    def make_old_siglum(self, data, **kwargs) -> OldSiglum:
        return OldSiglum(**data)


class ManuscriptSchema(Schema):
    id = fields.Integer(required=True)
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    old_sigla = fields.Nested(
        OldSiglumSchema,
        required=False,
        data_key="oldSigla",
        many=True,
        load_default=tuple(),
    )
    museum_number: fields.Field = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    accession = fields.String(required=True)
    period_modifier = ValueEnumField(
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
        TransliterationSchema, load_default=Transliteration()
    )
    unplaced_lines: fields.Field = fields.Nested(
        TransliterationSchema, load_default=Transliteration(), data_key="unplacedLines"
    )
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    joins = fields.Pluck(JoinsSchema, "fragments", load_default=Joins(), load_only=True)
    is_in_fragmentarium = fields.Boolean(
        load_default=False, data_key="isInFragmentarium", load_only=True
    )

    @validates_schema
    def validate_provenance(self, data, **kwargs):
        provenace = data["provenance"]
        period = data["period"]
        type_ = data["type"]
        if is_invalid_standard_text(provenace, period, type_):
            raise ValidationError(
                "period and type must be None if provenance is Standard Text"
            )
        elif is_invalid_non_standard_text(provenace, period, type_):
            raise ValidationError(
                "period and type must not be None if provenance is not Standard Text"
            )

    @post_load
    def make_manuscript(self, data: dict, **kwargs) -> Manuscript:
        return Manuscript(
            data["id"],
            data["siglum_disambiguator"],
            tuple(data["old_sigla"]),
            data["museum_number"],
            data["accession"],
            data["period_modifier"],
            data["period"],
            data["provenance"],
            data["type"],
            data["notes"],
            data["colophon"],
            data["unplaced_lines"],
            tuple(data["references"]),
            data["joins"],
            data["is_in_fragmentarium"],
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
        ParallelLineSchema, many=True, load_default=tuple(), data_key="parallelLines"
    )
    intertext: fields.Field = fields.Nested(
        OneOfNoteLinePartSchema, many=True, load_default=tuple()
    )

    @post_load
    def make_line_variant(self, data: dict, **kwargs) -> LineVariant:
        return LineVariant(
            tuple(data["reconstruction"]),
            data["note"],
            tuple(data["manuscripts"]),
            tuple(data["parallel_lines"]),
            tuple(data["intertext"]),
        )


class LineSchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    old_line_numbers = fields.Nested(
        OldLineNumberSchema, data_key="oldLineNumbers", many=True, load_default=tuple()
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
    translation = fields.Nested(TranslationLineSchema, many=True, load_default=tuple())

    @post_load
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["number"],
            tuple(data["variants"]),
            tuple(data["old_line_numbers"]),
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["translation"]),
        )


class DictionaryLineSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    text_name = fields.String(required=True, data_key="textName")
    chapter_name = fields.String(
        required=True, validate=validate.Length(min=1), data_key="chapterName"
    )
    stage = ValueEnumField(Stage, required=True)
    line = fields.Nested(LineSchema, required=True)
    manuscripts = fields.Nested(ManuscriptSchema, required=True, many=True)

    @post_load
    def make_dictionary_line(self, data: dict, **kwargs) -> DictionaryLine:
        return DictionaryLine(
            data["text_id"],
            data["text_name"],
            data["chapter_name"],
            data["stage"],
            data["line"],
            tuple(data["manuscripts"]),
        )


class DictionaryLinePaginationSchema(Schema):
    dictionary_lines = fields.Nested(
        DictionaryLineSchema,
        required=True,
        many=True,
        data_key="dictionaryLines",
    )
    total_count = fields.Integer(required=True, data_key="totalCount")


class ChapterSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    classification = ValueEnumField(Classification, required=True)
    stage = ValueEnumField(Stage, required=True)
    version = fields.String(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    text_name = fields.String(data_key="textName", load_only=True, load_default="")
    order = fields.Integer(required=True)
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    uncertain_fragments: fields.Field = fields.Nested(
        MuseumNumberSchema,
        many=True,
        load_default=tuple(),
        data_key="uncertainFragments",
    )
    lines = fields.Nested(LineSchema, many=True, required=True)
    signs = fields.List(fields.String(allow_none=True), load_default=tuple())
    record = fields.Nested(RecordSchema, load_default=Record())
    parser_version = fields.String(load_default="", data_key="parserVersion")
    is_filtered_query = fields.Bool(load_default=False, data_key="isFilteredQuery")
    colophon_lines_in_query = fields.Nested(
        ChapterQueryColophonLinesSchema,
        load_default={"colophonLinesInQuery": dict()},
        data_key="colophonLinesInQuery",
    )

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
    def make_uncertain_fragment(self, data: dict, **kwargs) -> UncertainFragment:
        return UncertainFragment(data["museum_number"])


class ChapterListingSchema(Schema):
    stage = ValueEnumField(Stage, required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    translation = fields.Nested(TranslationLineSchema, many=True, load_default=tuple())
    uncertain_fragments = fields.Nested(
        UncertainFragmentSchema,
        many=True,
        load_default=tuple(),
        data_key="uncertainFragments",
    )

    @post_load
    def make_chapter_listing(self, data: dict, **kwargs) -> ChapterListing:
        return ChapterListing(
            Stage(data["stage"]),
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
    references = fields.Nested(ReferenceSchema, many=True, load_default=tuple())
    projects = fields.List(ResearchProjectField(), load_default=tuple())

    @post_load
    def make_text(self, data: dict, **kwargs) -> Text:
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
        self, data: dict, **kwargs
    ) -> ManuscriptAttestation:
        return ManuscriptAttestation(
            data["text"],
            data["chapter_id"],
            data["manuscript"],
        )
