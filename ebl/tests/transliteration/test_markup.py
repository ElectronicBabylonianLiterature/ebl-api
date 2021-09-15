import pytest
from ebl.bibliography.domain.reference import Reference, ReferenceType, BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    MarkupPart,
    StringPart,
)
from ebl.transliteration.domain.sign_tokens import Divider

PUNCTUATION = ";,:.-–—"
LANGUAGE_PART = LanguagePart(Language.AKKADIAN, [Divider.of(":")])
BIBLIOGRAPHY_PART = BibliographyPart(
    Reference(BibliographyId("1"), ReferenceType.DISCUSSION, PUNCTUATION)
)


@pytest.mark.parametrize(  # pyre-ignore[56]
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
def test_rstrip(part: MarkupPart, expected: MarkupPart) -> None:
    assert part.rstrip() == expected
