from typing import Optional, Sequence, Tuple, Type

from lark.exceptions import ParseError, UnexpectedInput
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, validate

from ebl.corpus.application.schemas import (
    ChapterSchema,
    LineVariantSchema,
)
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.transliteration.application.line_number_schemas import OldLineNumberSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    parse_line_number,
    parse_note_line,
    parse_parallel_line,
    parse_translation_line,
)
from ebl.markup.domain.converters import markup_from_string
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.atf_parsers.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.corpus.web.chapter_manuscript_schemas import (
    ApiManuscriptLineSchema,
    ApiManuscriptSchema,
    ApiOldSiglumSchema,
    MuseumNumberString,
)

__all__ = [
    "ApiChapterSchema",
    "ApiLineSchema",
    "ApiLineVariantSchema",
    "ApiManuscriptLineSchema",
    "ApiManuscriptSchema",
    "ApiOldSiglumSchema",
    "MuseumNumberString",
]


class LineNumberString(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value.label, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return parse_line_number(deserialized)
        except (ValueError, ParseError, UnexpectedInput) as error:
            raise ValidationError("Invalid line number.", attr) from error


def _split_reconstruction(
    reconstruction: str,
) -> Tuple[str, Optional[str], Sequence[str]]:
    [text, *rest] = reconstruction.split("\n")
    note = rest[0] if rest and rest[0].startswith("#note:") else None
    parallel_lines = rest if note is None else rest[1:]
    return text, note, parallel_lines


RECONSTRUCTION_ERRORS: Tuple[Type[Exception], ...] = (*PARSE_ERRORS, ValueError)


def _parse_reconstruction(
    reconstruction: str,
) -> Tuple[Sequence[Token], Optional[NoteLine], Sequence[ParallelLine]]:
    try:
        text, note, parallel_lines = _split_reconstruction(reconstruction)
        return (
            parse_reconstructed_line(text),
            parse_note_line(note) if note else None,
            tuple(parse_parallel_line(line) for line in parallel_lines),
        )
    except RECONSTRUCTION_ERRORS as error:
        raise ValidationError(
            f"Invalid reconstruction: {reconstruction}. {error}"
        ) from error


class ApiLineVariantSchema(LineVariantSchema):
    class Meta:
        exclude = ("note", "parallel_lines")
        unknown = EXCLUDE

    reconstruction = fields.Function(
        lambda line: "".join(
            [
                convert_to_atf(None, line.reconstruction),
                f"\n{line.note.atf}" if line.note else "",
                *[f"\n{parallel_line.atf}" for parallel_line in line.parallel_lines],
            ]
        ),
        lambda value: value,
        required=True,
    )
    reconstructionTokens = fields.Nested(
        OneOfTokenSchema, many=True, attribute="reconstruction", dump_only=True
    )
    manuscripts = fields.Nested(ApiManuscriptLineSchema, many=True, required=True)
    intertext = fields.Function(
        lambda line: "".join(part.value for part in line.intertext),
        markup_from_string,
        load_default="",
    )

    @post_load
    def make_line_variant(self, data: dict, **kwargs) -> LineVariant:
        text, note, parallel_lines = _parse_reconstruction(data["reconstruction"])
        return LineVariant(
            text, note, tuple(data["manuscripts"]), parallel_lines, data["intertext"]
        )


def deserialize_translation(atf: str) -> Sequence[TranslationLine]:
    try:
        return (
            tuple(parse_translation_line(line) for line in atf.split("\n"))
            if atf
            else ()
        )
    except PARSE_ERRORS as error:
        raise ValidationError(f"Invalid translation: {atf}.", "translation") from error


class ApiLineSchema(Schema):
    number = LineNumberString(required=True)
    old_line_numbers = fields.Nested(
        OldLineNumberSchema, data_key="oldLineNumbers", many=True, load_default=()
    )
    variants = fields.Nested(
        ApiLineVariantSchema, many=True, required=True, validate=validate.Length(min=1)
    )
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    translation = fields.Function(
        lambda line: "\n".join(translation.atf for translation in line.translation),
        deserialize_translation,
        required=True,
    )

    @post_load
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["number"],
            tuple(data["variants"]),
            tuple(data["old_line_numbers"]),
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            data["translation"],
        )


class ApiChapterSchema(ChapterSchema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    uncertain_fragments = fields.List(
        MuseumNumberString(), load_default=(), data_key="uncertainFragments"
    )
    lines = fields.Nested(ApiLineSchema, many=True, required=True)
