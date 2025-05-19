from typing import Sequence, Dict
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.domain.lark_parser_errors import PARSE_ERRORS
from marshmallow import ValidationError
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_markup_paragraphs


def markup_from_string(string: str) -> Sequence[MarkupPart]:
    try:
        return parse_markup_paragraphs(string) if string else ()
    except PARSE_ERRORS as error:
        raise ValidationError(f"Invalid markup: {string}. {error}") from error


def markup_to_json(markup: Sequence[MarkupPart]) -> Sequence[Dict]:
    return [OneOfNoteLinePartSchema().dump(markup_part) for markup_part in markup]


def markup_string_to_json(string: str) -> Sequence[Dict]:
    return markup_to_json(markup_from_string(string))
