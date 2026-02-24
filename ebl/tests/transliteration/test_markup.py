from typing import Sequence

import pytest

from ebl.bibliography.domain.reference import Reference, ReferenceType, BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    MarkupPart,
    StringPart,
    rstrip,
    title_case,
    titlecase,
    to_title,
)
from ebl.transliteration.domain.sign_tokens import Divider, Reading

PUNCTUATION = ";,:.-–—"
TEXT = "sed nec tortor varius, iaculis."
LONG_TEXT = "Enkidu’s legs grew weary, whose [herd was] on [the move]"
LONG_TEXT_TITLECASE = "Enkidu’s Legs Grew Weary, Whose [Herd Was] On [The Move]"
LANGUAGE_PART = LanguagePart(
    Language.AKKADIAN, [Reading.of_name("kur"), Divider.of(":")]
)
BIBLIOGRAPHY_PART = BibliographyPart(
    Reference(BibliographyId("1"), ReferenceType.DISCUSSION, TEXT + PUNCTUATION)
)


@pytest.mark.parametrize(
    "part,expected",
    [
        (
            StringPart(f"{PUNCTUATION}A{PUNCTUATION}A{PUNCTUATION}"),
            StringPart(f"{PUNCTUATION}A{PUNCTUATION}A"),
        ),
        (
            EmphasisPart(f"{PUNCTUATION}A{PUNCTUATION}A{PUNCTUATION}"),
            EmphasisPart(f"{PUNCTUATION}A{PUNCTUATION}A"),
        ),
        (LANGUAGE_PART, LANGUAGE_PART),
        (BIBLIOGRAPHY_PART, BIBLIOGRAPHY_PART),
    ],
)
def test_part_rstrip(part: MarkupPart, expected: MarkupPart) -> None:
    assert part.rstrip() == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        (LONG_TEXT, LONG_TEXT_TITLECASE),
    ],
)
def test_titlecase(text: str, expected: str) -> None:
    assert titlecase(text) == expected


@pytest.mark.parametrize(
    "part,expected",
    [
        (StringPart(TEXT), StringPart(titlecase(TEXT))),
        (EmphasisPart(TEXT), EmphasisPart(titlecase(TEXT))),
        (
            StringPart(LONG_TEXT),
            StringPart(LONG_TEXT_TITLECASE),
        ),
        (LANGUAGE_PART, LANGUAGE_PART),
        (BIBLIOGRAPHY_PART, BIBLIOGRAPHY_PART),
        (
            StringPart("ṣome špecial cḫaracterš ḫere and ṭhere"),
            StringPart("Ṣome Špecial Cḫaracterš Ḫere And Ṭhere"),
        ),
    ],
)
def test_part_title_case(part: MarkupPart, expected: MarkupPart) -> None:
    assert part.title_case() == expected


@pytest.mark.parametrize(
    "parts,expected",
    [
        ((), ()),
        ([StringPart("foo--")], (StringPart("foo"),)),
        (
            [StringPart("foo--"), StringPart("foo--")],
            (StringPart("foo--"), StringPart("foo")),
        ),
    ],
)
def test_rstrip(parts: Sequence[MarkupPart], expected: Sequence[MarkupPart]) -> None:
    assert rstrip(parts) == expected


@pytest.mark.parametrize(
    "parts,expected",
    [((), ()), ([StringPart("foo bar")], (StringPart("Foo Bar"),))],
)
def test_title_case(
    parts: Sequence[MarkupPart], expected: Sequence[MarkupPart]
) -> None:
    assert title_case(parts) == expected


@pytest.mark.parametrize(
    "parts,expected",
    [
        (
            [StringPart("t"), EmphasisPart("["), StringPart("igris")],
            [StringPart("T"), EmphasisPart("["), StringPart("igris")],
        ),
    ],
)
@pytest.mark.xfail(
    reason="Token-internal StringParts are always capitalized but in this case shouldn't."
)
def test_context_aware_title_case(
    parts: Sequence[MarkupPart], expected: Sequence[MarkupPart]
) -> None:
    assert title_case(parts) == expected


@pytest.mark.parametrize("parts", [(), [StringPart("foo-- bar--")]])
def test_to_title(parts: Sequence[MarkupPart]) -> None:
    assert to_title(parts) == title_case(rstrip(parts))
