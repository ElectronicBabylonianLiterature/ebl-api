import pytest
from ebl.bibliography.domain.reference import BibliographyId
from ebl.tests.transliteration.test_parse_note_line import expected_language_part
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_markup_paragraphs
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    BoldPart,
    EmphasisPart,
    ParagraphPart,
    StringPart,
    SubscriptPart,
    SuperscriptPart,
    UrlPart,
)


@pytest.mark.parametrize(
    "atf,expected",
    [
        (
            "A simple, one-line introduction",
            (StringPart("A simple, one-line introduction"),),
        ),
        ("\tExtra\n whitespace  ", (StringPart("Extra whitespace"),)),
        ("Very @i{important}", (StringPart("Very "), EmphasisPart("important"))),
        ("Very @b{important}", (StringPart("Very "), BoldPart("important"))),
        ("H@sup{2}O", (StringPart("H"), SuperscriptPart("2"), StringPart("O"))),
        ("CO@sub{2}", (StringPart("CO"), SubscriptPart("2"))),
        ("@akk{{d}kur}", (expected_language_part(Language.AKKADIAN, "{d}kur"),)),
        ("@sux{kur}", (expected_language_part(Language.SUMERIAN, "kur"),)),
        ("@es{kur}", (expected_language_part(Language.EMESAL, "kur"),)),
        (
            "@bib{RN123@x 2-3a}",
            (BibliographyPart.of(BibliographyId("RN123"), "x 2-3a"),),
        ),
        (
            "@bib{NO_PAGES}",
            (BibliographyPart.of(BibliographyId("NO_PAGES"), ""),),
        ),
        (
            "First paragraph.\n\nSecond.\n\n\nLast.\n\n",
            (
                StringPart("First paragraph."),
                ParagraphPart(),
                StringPart("Second."),
                ParagraphPart(),
                StringPart("Last."),
            ),
        ),
        (
            "A bare link: @url{http://www.example.com}",
            (
                StringPart("A bare link: "),
                UrlPart("", "http://www.example.com"),
            ),
        ),
        (
            "A link with @url{www.example.com}{a display text}",
            (
                StringPart("A link with "),
                UrlPart("a display text", "www.example.com"),
            ),
        ),
        (
            "@url{www.example.com/#špecial cḫars}",
            (UrlPart("", "www.example.com/#špecial cḫars"),),
        ),
    ],
)
def test_parse_markup_paragraphs(atf, expected) -> None:
    assert parse_markup_paragraphs(atf) == expected
