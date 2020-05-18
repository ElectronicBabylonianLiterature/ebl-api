import pytest  # pyre-ignore

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import LINE_PARSER, parse_atf_lark
from ebl.transliteration.domain.note_line import (BibliographyPart,
                                                  EmphasisPart, LanguagePart,
                                                  NoteLine, StringPart)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line_transformer import \
    TextLineTransformer


def parse_text(atf: str):
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__text")
    return TextLineTransformer().transform(tree)  # pyre-ignore[16]


def expected_language_part(language: Language, transliteration: str) -> LanguagePart:
    return LanguagePart.of_transliteration(language, parse_text(transliteration))


@pytest.mark.parametrize(
    "atf,expected_line",
    [
        ("#note: this is a note ", NoteLine([StringPart("this is a note "),]),),
        ("#note: @i{italic text}", NoteLine([EmphasisPart("italic text"),]),),
        (
            "#note: @akk{{d}kur}",
            NoteLine([expected_language_part(Language.AKKADIAN, "{d}kur"),]),
        ),
        (
            "#note: @sux{kur}",
            NoteLine([expected_language_part(Language.SUMERIAN, "kur"),]),
        ),
        (
            "#note: @es{kur}",
            NoteLine([expected_language_part(Language.EMESAL, "kur"),]),
        ),
        (            "#note: @bib{RN123@x 2-3a}",
            NoteLine([BibliographyPart.of("RN123", "x 2-3a")]),
        ),
        (
            "#note: @bib{RN1}@2}",
            NoteLine([BibliographyPart.of("RN1}", "2")]),
        ),
        (
            "#note: @bib{RN1@1}2}",
            NoteLine([BibliographyPart.of("RN1", "1}2")]),
        ),
        (
            "#note: @bib{RN12@3@3}",
            NoteLine([BibliographyPart.of("RN12@3", "3")]),
        ),
        (
            "#note: @bib{RN@1}@2}",
            NoteLine([BibliographyPart.of("RN", "1}@2")]),
        ),
        (
            (
                "#note: this is a note "
                "@i{italic text}@akk{kur}@sux{kur}"
            ),
            NoteLine(
                [
                    StringPart("this is a note "),
                    EmphasisPart("italic text"),
                    expected_language_part(Language.AKKADIAN, "kur"),
                    expected_language_part(Language.SUMERIAN, "kur"),
                ]
            ),
        ),
    ],
)
def test_parse_note_line(atf, expected_line) -> None:
    assert parse_atf_lark(atf).lines == Text.of_iterable([expected_line]).lines
