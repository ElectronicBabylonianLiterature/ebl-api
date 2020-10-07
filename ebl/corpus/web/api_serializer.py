from typing import cast, Sequence

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]

from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.corpus.domain.text import Line, Manuscript, ManuscriptLine, Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token
from ebl.errors import DataError
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.labels import parse_label, LineNumberLabel
from ebl.transliteration.domain.lark_parser import parse_line, parse_line_number
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.corpus.application.schemas import ApiManuscriptSchema


class ApiSerializer(TextSerializer):
    def __init__(self):
        super().__init__(ApiManuscriptSchema)

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer()
        serializer.visit_text(text)
        return serializer.text

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        line = manuscript_line.line
        atf_line_number = line.line_number.atf
        self.line["manuscripts"].append(
            {
                "manuscriptId": manuscript_line.manuscript_id,
                "labels": [label.to_value() for label in manuscript_line.labels],
                "number": LineNumberLabel.from_atf(atf_line_number).to_value(),
                "atf": line.atf[len(atf_line_number) + 1 :],
                # pyre-ignore[16]
                "atfTokens": TextLineSchema().dump(manuscript_line.line)["content"],
            }
        )

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
            tuple(
                self.deserialize_manuscript_line(line) for line in line["manuscripts"]
            ),
        )

    def deserialize_manuscript_line(self, manuscript_line: dict) -> ManuscriptLine:
        line_number = LineNumberLabel(manuscript_line["number"]).to_atf()
        atf = manuscript_line["atf"]
        line = cast(TextLine, parse_line(f"{line_number} {atf}"))
        return ManuscriptLine(
            manuscript_line["manuscriptId"],
            tuple(parse_label(label) for label in manuscript_line["labels"]),
            line,
        )


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
