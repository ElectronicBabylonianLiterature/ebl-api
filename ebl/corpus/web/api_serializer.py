from typing import Sequence

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]

from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.corpus.domain.text import Line, Manuscript, ManuscriptLine, Text
from ebl.transliteration.domain.tokens import Token
from ebl.errors import DataError
from ebl.transliteration.domain.lark_parser import parse_line_number
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.corpus.application.schemas import ApiManuscriptLineSchema, ApiManuscriptSchema
from ebl.transliteration.domain.labels import LineNumberLabel


class ApiSerializer(TextSerializer):
    def __init__(self):
        super().__init__(ApiManuscriptSchema)

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer()
        serializer.visit_text(text)
        return serializer.text

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        # pyre-ignore[16]
        self.line["manuscripts"].append(ApiManuscriptLineSchema().dump(manuscript_line))

    def visit_line(self, line: Line) -> None:
        super().visit_line(line)
        self.line["reconstructionTokens"] = [
            self._serialize_token(token) for token in line.reconstruction
        ]
        self.line["number"] = LineNumberLabel.from_atf(line.number.atf).to_value()

    def _serialize_token(self, token: Token) -> dict:
        return {"type": type(token).__name__, "value": token.value}


class ApiDeserializer(TextDeserializer):
    def deserialize_manuscript(self, manuscript: dict) -> Manuscript:
        return ApiManuscriptSchema().load(manuscript)  # pyre-ignore[16]

    def deserialize_line(self, line: dict) -> Line:
        return Line(
            parse_line_number(line["number"]),
            parse_reconstructed_line(line["reconstruction"]),
            False,
            False,
            tuple(
                self.deserialize_manuscript_line(line) for line in line["manuscripts"]
            ),
        )

    def deserialize_manuscript_line(self, manuscript_line: dict) -> ManuscriptLine:
        return ApiManuscriptLineSchema().load(manuscript_line)  # pyre-ignore[16]


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
