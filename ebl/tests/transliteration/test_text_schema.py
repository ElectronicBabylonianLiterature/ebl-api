import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.application.line_schemas import dump_lines
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.enclosure_tokens import Determinative, Erasure
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    LineContinuation,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word


def test_dump_line():
    text = Text(
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
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
        "lines": dump_lines(text.lines),
        "parser_version": text.parser_version,
    }


@pytest.mark.parametrize(
    "lines",
    [
        [EmptyLine()],
        [ControlLine.of_single("$", ValueToken.of(" single ruling"))],
        [
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
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
                    LineContinuation.of("→"),
                ],
            )
        ],
    ],
)
def test_load_line(lines):
    parser_version = "2.3.1"
    serialized_lines = dump_lines(lines)
    assert TextSchema().load(
        {"lines": serialized_lines, "parser_version": parser_version,}
    ) == Text.of_iterable(lines).set_parser_version(parser_version)
