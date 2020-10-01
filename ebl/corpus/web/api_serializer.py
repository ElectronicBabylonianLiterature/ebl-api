from typing import cast, Sequence

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore

from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.transliteration.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
)
from ebl.corpus.domain.text import Line, ManuscriptLine, Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token
from ebl.errors import DataError
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.labels import parse_label, LineNumberLabel
from ebl.transliteration.domain.lark_parser import parse_line, parse_line_number
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)


class ApiSerializer(TextSerializer):
    def __init__(self, include_documents=True):
        super().__init__(include_documents)

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer(False)
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
        self.line["reconstructionTokens"] = []
        self.line["number"] = LineNumberLabel.from_atf(line.number.atf).to_value()

    def visit(self, token: Token) -> None:
        self._visit_reconstruction_token(type(token).__name__, token)

    def visit_akkadian_word(self, word: AkkadianWord):
        self._visit_reconstruction_token("AkkadianWord", word)

    def visit_lacuna(self, lacuna: Lacuna) -> None:
        self._visit_reconstruction_token("Lacuna", lacuna)

    def visit_metrical_foot_separator(self, separator: MetricalFootSeparator) -> None:
        self._visit_reconstruction_token("MetricalFootSeparator", separator)

    def visit_caesura(self, caesura: Caesura) -> None:
        self._visit_reconstruction_token("Caesura", caesura)

    def _visit_reconstruction_token(self, type: str, token: Token) -> None:
        self.line["reconstructionTokens"].append({"type": type, "value": token.value})


class ApiDeserializer(TextDeserializer):
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


def serialize(text: Text, include_documents=True) -> dict:
    return ApiSerializer.serialize(text, include_documents)


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
