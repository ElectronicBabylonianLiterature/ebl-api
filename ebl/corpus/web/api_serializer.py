from typing import Sequence

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]
from marshmallow import EXCLUDE  # pyre-ignore[21]

from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.corpus.domain.text import Line, Manuscript, Text
from ebl.errors import DataError
from ebl.corpus.application.schemas import ApiLineSchema, ApiManuscriptSchema


class ApiSerializer(TextSerializer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer()
        serializer.visit_text(text)
        return serializer.text

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        # pyre-ignore[16]
        self.chapter["manuscripts"].append(ApiManuscriptSchema().dump(manuscript))

    def visit_line(self, line: Line) -> None:
        self.chapter["lines"].append(ApiLineSchema().dump(line))  # pyre-ignore[16]


class ApiDeserializer(TextDeserializer):
    def deserialize_manuscript(self, manuscript: dict) -> Manuscript:
        return ApiManuscriptSchema().load(manuscript)  # pyre-ignore[16]

    def deserialize_line(self, line: dict) -> Line:
        return ApiLineSchema().load(line, unknown=EXCLUDE)  # pyre-ignore[16]


def serialize(text: Text) -> dict:
    return ApiSerializer.serialize(text)


def deserialize(dto: dict) -> Text:
    try:
        return ApiDeserializer.deserialize(dto)
    except (ValueError, ParseError, UnexpectedInput) as error:
        raise DataError(error)


def deserialize_lines(lines: list) -> Sequence[Line]:
    deserializer = ApiDeserializer()
    try:
        return tuple(deserializer.deserialize_line(line) for line in lines)
    except (ValueError, ParseError, UnexpectedInput) as error:
        raise DataError(error)
