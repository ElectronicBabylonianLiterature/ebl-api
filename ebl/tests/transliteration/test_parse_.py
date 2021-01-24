from typing import List

import pytest

from ebl.corpus.domain.chapter import Line
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Divider, Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LineBreak, Joiner, \
    EgyptianMetricalFeetSeparator
from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(  # pyre-ignore[56]
    "line,expected_tokens",
    [
            (
                    "1. a << • >> * a",
             [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            [
                                Reading.of_name("a"),

                            ]
                        ),
                        EgyptianMetricalFeetSeparator.of(),
                        Word.of(
                            [
                                Reading.of_name("a"),

                            ]
                        ),
                    ),
                )
            ]
            )
    ],
)
def test_invalid_text_line(line: str, expected_tokens: List[Line]) -> None:
    x = parse_atf_lark(line).lines
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines
