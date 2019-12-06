from typing import Tuple

from parsy import ParseError

from ebl.corpus.application.text_serializer import (
    TextDeserializer,
    TextSerializer,
)
from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
    ReconstructionToken,
)
from ebl.corpus.domain.text import Line, ManuscriptLine, Text
from ebl.errors import DataError
from ebl.transliteration.domain.labels import Label, LineNumberLabel
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line_schemas import dump_line


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
        self.line["manuscripts"].append(
            {
                "manuscriptId": manuscript_line.manuscript_id,
                "labels": [label.to_value() for label in manuscript_line.labels],
                "number": line.line_number.to_value(),
                "atf": line.atf[len(line.line_number.to_atf()) + 1 :],
                "atfTokens": dump_line(manuscript_line.line)["content"],
            }
        )

    def visit_line(self, line: Line) -> None:
        super().visit_line(line)
        self.line["reconstructionTokens"] = []

    def visit_akkadian_word(self, word: AkkadianWord):
        self._visit_reconstruction_token("AkkadianWord", word)

    def visit_lacuna(self, lacuna: Lacuna) -> None:
        self._visit_reconstruction_token("Lacuna", lacuna)

    def visit_metrical_foot_separator(self, separator: MetricalFootSeparator) -> None:
        self._visit_reconstruction_token("MetricalFootSeparator", separator)

    def visit_caesura(self, caesura: Caesura) -> None:
        self._visit_reconstruction_token("Caesura", caesura)

    def _visit_reconstruction_token(
        self, type: str, token: ReconstructionToken
    ) -> None:
        self.line["reconstructionTokens"].append({"type": type, "value": str(token)})


class ApiDeserializer(TextDeserializer):
    def deserialize_manuscript_line(self, manuscript_line: dict) -> ManuscriptLine:
        line_number = LineNumberLabel(manuscript_line["number"]).to_atf()
        atf = manuscript_line["atf"]
        line = parse_line(f"{line_number} {atf}")
        return ManuscriptLine(
            manuscript_line["manuscriptId"],
            tuple(Label.parse(label) for label in manuscript_line["labels"]),
            line,
        )


def serialize(text: Text, include_documents=True) -> dict:
    return ApiSerializer.serialize(text, include_documents)


def deserialize(dto: dict) -> Text:
    try:
        return ApiDeserializer.deserialize(dto)
    except (ValueError, ParseError) as error:
        raise DataError(error)


def deserialize_lines(lines: list) -> Tuple[Line, ...]:
    deserializer = ApiDeserializer()
    try:
        return tuple(deserializer.deserialize_line(line) for line in lines)
    except (ValueError, ParseError) as error:
        raise DataError(error)
