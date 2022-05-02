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
    to_title,
)
from ebl.transliteration.domain.sign_tokens import Divider, Reading

PUNCTUATION = ";,:.-–—"
TEXT = "sed nec tortor varius, iaculis."
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
    "part,expected",
    [
        (StringPart(TEXT), StringPart(TEXT.title())),
        (EmphasisPart(TEXT), EmphasisPart(TEXT.title())),
        (LANGUAGE_PART, LANGUAGE_PART),
        (BIBLIOGRAPHY_PART, BIBLIOGRAPHY_PART),
    ],
)
def test_part_title_case(part: MarkupPart, expected: MarkupPart) -> None:
    assert part.title_case() == expected


@pytest.mark.parametrize(
    "parts,expected",
    [
        (tuple(), tuple()),
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
    [(tuple(), tuple()), ([StringPart("foo bar")], (StringPart("Foo Bar"),))],
)
def test_title_case(
    parts: Sequence[MarkupPart], expected: Sequence[MarkupPart]
) -> None:
    assert title_case(parts) == expected


@pytest.mark.parametrize("parts", [tuple(), [StringPart("foo-- bar--")]])
def test_to_title(parts: Sequence[MarkupPart]) -> None:
    assert to_title(parts) == title_case(rstrip(parts))
