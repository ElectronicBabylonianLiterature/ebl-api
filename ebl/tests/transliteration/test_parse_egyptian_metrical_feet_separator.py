from typing import List

import pytest

from ebl.corpus.domain.chapter import Line
from ebl.transliteration.domain.atf import Atf, Flag
from ebl.transliteration.domain.enclosure_tokens import Removal
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner

from ebl.transliteration.domain.word_tokens import Word


@pytest.mark.parametrize(  # pyre-ignore[56]
    "line,expected_tokens",
    [
        (
            "1. •",
            [TextLine.of_iterable(LineNumber(1), (Word.of((Reading.of_name("•"),)),))],
        ),
        (
            "1. a • a",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of((Reading.of_name("a"),)),
                        Word.of((Reading.of_name("•"),)),
                        Word.of((Reading.of_name("a"),)),
                    ),
                )
            ],
        ),
        (
            "1. a-<<•>>-a",
            [
                TextLine.of_iterable(
                    LineNumber(1), (
                            Word.of(parts=[
                                Reading.of_name("a"),
                                Joiner.hyphen(),
                                Removal.open(),
                                Reading.of_name("•"),
                                Removal.close(),
                                Joiner.hyphen(),
                                Reading.of_name("a"),
                            ]),)
                )
            ],
        ),
        (
                "1. •*",
                [
                    TextLine.of_iterable(
                        LineNumber(1),
                        (
                                Word.of((Reading.of_name("•", flags=(Flag.COLLATION,)),)),
                        ),
                    )
                ],
        ),
    ],
)
def test_egpytian_feet_metrical_feet_line(
    line: str, expected_tokens: List[Line]
) -> None:
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize(
    "atf,",
    [
        "1. a-(•*)-a",
        "1. (•)",
        "1. [(•)]",
        "1. a • a",
        "1. •",
        "1. a-na-ku • a-ka-na • ep-še-e-ku • ma-an#-nu • i-lu • še-na • ša i-na (•) ma-a-ti •",
        "1. ha-al-qu₂ • {d}dumu#-zi •* u₃ {d}giz-zi-da • šu-nu • a-ha-mi-iš • ip-pa-la-su₂-ma •",
        "1. iṣ-ṣe#-ne₂-eh-hu • šu-nu • a-ma-ta da-mi-iq-ta •",
        "1. a-na# {d}a-ni • i#-qa₂#-ab-bu-u₂ • pa-<<•>>-ni • ba-nu-ti •* ša {d}a-ni •",
    ],
)  # pyre-ignore[56]
def test_egpytian_feet_metrical_feet_line_atf(atf: Atf) -> None:
    line = parse_atf_lark(atf)
    assert line.atf == atf
