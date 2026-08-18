from typing import Any, Dict, cast

from marshmallow import Schema, ValidationError, fields, post_load

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import (
    ManuscriptSchema,
    OldSiglumSchema,
    labels,
    manuscript_id,
)
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.parser import parse_paratext
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    TransliterationError,
    parse_atf_lark,
    parse_text_line,
)
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text_line import TextLine


class MuseumNumberString(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(str(value) if value else "", attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return MuseumNumber.of(deserialized) if deserialized else None
        except ValueError as error:
            raise ValidationError("Invalid museum number.", attr) from error


def _deserialize_transliteration(value):
    try:
        return parse_atf_lark(value)
    except TransliterationError as error:
        raise ValidationError(f"Invalid colophon: {value}.", "colophon") from error


class ApiOldSiglumSchema(OldSiglumSchema):
    reference = fields.Nested(ApiReferenceSchema, required=True)


class ApiManuscriptSchema(ManuscriptSchema):
    old_sigla = fields.Nested(
        ApiOldSiglumSchema,
        many=True,
        required=False,
        load_default=(),
        data_key="oldSigla",
    )
    museum_number = MuseumNumberString(required=True, data_key="museumNumber")
    colophon = fields.Function(
        lambda manuscript: manuscript.colophon.atf,
        _deserialize_transliteration,
        required=True,
    )
    unplaced_lines = fields.Function(
        lambda manuscript: manuscript.unplaced_lines.atf,
        _deserialize_transliteration,
        required=True,
        data_key="unplacedLines",
    )
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)
    joins = fields.Pluck(JoinsSchema, "fragments", load_default=Joins())
    is_in_fragmentarium = fields.Boolean(
        load_default=False, data_key="isInFragmentarium"
    )


def _serialize_number(manuscript_line: ManuscriptLine) -> str:
    return (
        manuscript_line.line.line_number.label
        if isinstance(manuscript_line.line, TextLine)
        else ""
    )


def _strip_line_number(line: TextLine) -> str:
    start = len(line.line_number.atf) + 1
    return line.atf[start:]


def _serialize_atf(manuscript_line: ManuscriptLine) -> str:
    return "\n".join(
        [
            (
                _strip_line_number(manuscript_line.line)
                if isinstance(manuscript_line.line, TextLine)
                else ""
            ),
            *[line.atf for line in manuscript_line.paratext],
        ]
    ).strip()


def _serialize_atf_tokens(manuscript_line) -> Any:
    dumped = cast(Dict[str, Any], OneOfLineSchema().dump(manuscript_line.line))
    return dumped["content"]


class ApiManuscriptLineSchema(Schema):
    manuscript_id = manuscript_id()
    labels = labels()
    number = fields.Function(_serialize_number, lambda value: value, required=True)
    atf = fields.Function(_serialize_atf, lambda value: value, required=True)
    atfTokens = fields.Function(_serialize_atf_tokens, lambda value: value)
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        has_text_line = len(data["number"]) > 0
        lines = data["atf"].split("\n")
        provenance_service = self.context.get("provenance_service")
        if provenance_service is None:
            raise ValidationError("Provenance service not configured.")
        try:
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
                tuple(parse_paratext(line, provenance_service) for line in paratext),
                tuple(data["omitted_words"]),
            )
        except PARSE_ERRORS as error:
            raise ValidationError(
                f"Invalid manuscript line: {data['atf']}.", "atf"
            ) from error
