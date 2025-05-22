import pytest

from ebl.bibliography.domain.reference import BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import (
    LINE_PARSER,
    parse_atf_lark,
    parse_markup,
)
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    StringPart,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer


def parse_text(atf: str):
    tree = LINE_PARSER.parse(atf, start="text_line__text")
    return TextLineTransformer().transform(tree)


def expected_language_part(language: Language, transliteration: str) -> LanguagePart:
    return LanguagePart.of_transliteration(language, parse_text(transliteration))


@pytest.mark.parametrize(
    "atf,expected",
    [
        ("this is a note ", (StringPart("this is a note "),)),
        ("@i{italic text}", (EmphasisPart("italic text"),)),
        ("@akk{{d}kur}", (expected_language_part(Language.AKKADIAN, "{d}kur"),)),
        ("@sux{kur}", (expected_language_part(Language.SUMERIAN, "kur"),)),
        ("@es{kur}", (expected_language_part(Language.EMESAL, "kur"),)),
        (
            "@bib{RN123@x 2-3a}",
            (BibliographyPart.of(BibliographyId("RN123"), "x 2-3a"),),
        ),
        ("@bib{RN1\\}@2}", (BibliographyPart.of(BibliographyId("RN1}"), "2"),)),
        ("@bib{RN1@1\\}2}", (BibliographyPart.of(BibliographyId("RN1"), "1}2"),)),
        ("@bib{RN12\\@3@3}", (BibliographyPart.of(BibliographyId("RN12@3"), "3"),)),
        ("@bib{RN@1\\}\\@2}", (BibliographyPart.of(BibliographyId("RN"), "1}@2"),)),
        ("@bib{RN}", (BibliographyPart.of(BibliographyId("RN"), ""),)),
        (
            "this is a note @i{italic text}@akk{kur}@sux{kur}",
            (
                StringPart("this is a note "),
                EmphasisPart("italic text"),
                expected_language_part(Language.AKKADIAN, "kur"),
                expected_language_part(Language.SUMERIAN, "kur"),
            ),
        ),
    ],
)
def test_parse_markup(atf, expected) -> None:
    assert parse_markup(atf) == expected


def test_parse_note_line() -> None:
    markup = "this is a note @i{italic text}@akk{kur}@sux{kur}"
    atf = f"#note: {markup}"
    expected_line = NoteLine(parse_markup(markup))
    assert parse_atf_lark(atf).lines == Text.of_iterable([expected_line]).lines
