import pytest  # pyre-ignore

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.enclosure_tokens import Determinative, Erasure
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word


def test_dump_line():
    text = Text(
        (
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        parts=[
                            Reading.of_name("ha"),
                            Joiner.hyphen(),
                            Reading.of_name("am"),
                        ],
                    )
                ],
            ),
            EmptyLine(),
            ControlLine.of_single("$", ValueToken.of(" single ruling")),
        ),
        "1.0.0",
    )

    assert TextSchema().dump(text) == {
        "lines": OneOfLineSchema().dump(text.lines, many=True),
        "parser_version": text.parser_version,
        "number_of_lines": text.number_of_lines,
    }


@pytest.mark.parametrize(
    "lines",
    [
        [EmptyLine()],
        [ControlLine.of_single("$", ValueToken.of(" single ruling"))],
        [
            TextLine.of_iterable(
                LineNumber(1),
                [
                    Word.of(
                        unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("nu")],
                    ),
                    Word.of(alignment=1, parts=[Reading.of_name("nu")]),
                    LanguageShift.of("%sux"),
                    LoneDeterminative.of(
                        [Determinative.of([Reading.of_name("nu")])],
                        language=Language.SUMERIAN,
                    ),
                    Erasure.open(),
                    Erasure.center(),
                    Erasure.close(),
                ],
            )
        ],
    ],
)
def test_load_line(lines):
    parser_version = "2.3.1"
    serialized_lines = OneOfLineSchema().dump(lines, many=True)
    assert TextSchema().load(
        {"lines": serialized_lines, "parser_version": parser_version, "number_of_lines": len(serialized_lines)}
    ) == Text.of_iterable(lines).set_parser_version(parser_version)

