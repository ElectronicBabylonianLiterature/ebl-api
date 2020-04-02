import pytest  # pyre-ignore

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.note_line import (
    NoteLine,
    StringPart,
    EmphasisPart,
    LanguagePart,
)
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize(
    "atf,expected_line",
    [
        ("#note: this is a note ", NoteLine([StringPart("this is a note "),]),),
        ("#note: @i{italic text}", NoteLine([EmphasisPart("italic text"),]),),
        (
            "#note: @akk{Akkadian language}",
            NoteLine([LanguagePart("Akkadian language", Language.AKKADIAN),]),
        ),
        (
            "#note: @sux{Sumerian language}",
            NoteLine([LanguagePart("Sumerian language", Language.SUMERIAN),]),
        ),
        (
            (
                "#note: this is a note "
                "@i{italic text}@akk{Akkadian language}@sux{Sumerian language}"
            ),
            NoteLine(
                [
                    StringPart("this is a note "),
                    EmphasisPart("italic text"),
                    LanguagePart("Akkadian language", Language.AKKADIAN),
                    LanguagePart("Sumerian language", Language.SUMERIAN),
                ]
            ),
        ),
    ],
)
def test_parse_note_line(atf, expected_line):
    assert parse_atf_lark(atf).lines == Text.of_iterable([expected_line]).lines
