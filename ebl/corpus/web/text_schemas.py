from typing import Optional, Sequence, Tuple, cast

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]
from marshmallow import (  # pyre-ignore[21]
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
)

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import (
    ChapterSchema,
    LineVariantSchema,
    ManuscriptSchema,
    TextSchema,
    labels,
    manuscript_id,
)
from ebl.corpus.domain.chapter import Line, LineVariant, ManuscriptLine
from ebl.errors import DataError
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.lark_parser import (
    PARSE_ERRORS,
    parse_line_number,
    parse_note_line,
    parse_parallel_line,
    parse_paratext,
    parse_text_line,
)
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token


class MuseumNumberString(fields.String):  # pyre-ignore[11]
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(str(value) if value else "", attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return MuseumNumber.of(deserialized) if deserialized else None
        except ValueError as error:
            raise ValidationError("Invalid museum number.") from error


class ApiManuscriptSchema(ManuscriptSchema):
    # pyre-ignore[28]
    museum_number = MuseumNumberString(required=True, data_key="museumNumber")
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)


def _serialize_number(manuscript_line: ManuscriptLine) -> str:
    return (
        cast(TextLine, manuscript_line.line).line_number.label
        if isinstance(manuscript_line.line, TextLine)
        else ""
    )


def _serialize_atf(manuscript_line: ManuscriptLine) -> str:
    return "\n".join(
        [
            manuscript_line.line.atf[
                len(cast(TextLine, manuscript_line.line).line_number.atf) + 1 :
            ]
            if isinstance(manuscript_line.line, TextLine)
            else "",
            *[line.atf for line in manuscript_line.paratext],
        ]
    ).strip()


class ApiManuscriptLineSchema(Schema):  # pyre-ignore[11]
    manuscript_id = manuscript_id()
    labels = labels()
    number = fields.Function(_serialize_number, lambda value: value, required=True)
    atf = fields.Function(_serialize_atf, lambda value: value, required=True)
    atfTokens = fields.Function(
        # pyre-ignore[16]
        lambda manuscript_line: OneOfLineSchema().dump(manuscript_line.line)["content"],
        lambda value: value,
    )
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load  # pyre-ignore[56]
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        has_text_line = len(data["number"]) > 0
        lines = data["atf"].split("\n")
        text = (
            parse_text_line(f"{data['number']}. {lines[0]}")
            if has_text_line
            else EmptyLine()
        )
        paratext = lines[1:] if has_text_line else lines
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            text,
            tuple(parse_paratext(line) for line in paratext),
            tuple(data["omitted_words"]),
        )


class LineNumberString(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value.label, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return parse_line_number(deserialized)
        except (ValueError, ParseError, UnexpectedInput) as error:
            raise ValidationError("Invalid line number.") from error


def _split_reconstruction(
    reconstruction: str
) -> Tuple[str, Optional[str], Sequence[str]]:
    [text, *rest] = reconstruction.split("\n")
    note = rest[0] if rest and rest[0].startswith("#note:") else None
    parallel_lines = rest if note is None else rest[1:]
    return text, note, parallel_lines


def _parse_recontsruction(
    reconstruction: str
) -> Tuple[Sequence[Token], Optional[NoteLine], Sequence[ParallelLine]]:
    try:
        text, note, parallel_lines = _split_reconstruction(reconstruction)
        return (
            parse_reconstructed_line(text),
            note and parse_note_line(note),
            tuple(parse_parallel_line(line) for line in parallel_lines),
        )
    except PARSE_ERRORS as error:
        raise DataError(f"Invalid reconstruction: {reconstruction}. {error}")


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

    @post_load  # pyre-ignore[56]
    def make_line_variant(self, data: dict, **kwargs) -> LineVariant:
        text, note, parallel_lines = _parse_recontsruction(data["reconstruction"])
        return LineVariant(text, note, tuple(data["manuscripts"]), parallel_lines)


class ApiLineSchema(Schema):
    number = LineNumberString(required=True)  # pyre-ignore[28]
    variants = fields.Nested(
        ApiLineVariantSchema, many=True, required=True, validate=validate.Length(min=1)
    )
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )

    @post_load  # pyre-ignore[56]
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["number"],
            tuple(data["variants"]),
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
        )


class ApiChapterSchema(ChapterSchema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    uncertain_fragments = fields.List(
        MuseumNumberString(), missing=tuple(), data_key="uncertainFragments"
    )
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


class ApiTextSchema(TextSchema):
    chapters = fields.Nested(ApiChapterSchema, many=True, required=True)
