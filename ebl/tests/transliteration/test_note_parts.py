import pytest

from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.transliteration.domain.note_line import BibliographyPart

BIBLIOGRAPHY_ID = BibliographyId("ABC")


def test_bibliography_part() -> None:
    pages = "12-49"
    part = BibliographyPart.of(BIBLIOGRAPHY_ID, pages)

    assert part.reference == Reference(
        BIBLIOGRAPHY_ID, ReferenceType.DISCUSSION, pages, "", tuple()
    )


def test_bibliography_part_escape() -> None:
    unescaped = "@{\\}"
    escaped = "\\@\\{\\\\\\}"
    part = BibliographyPart.of(BibliographyId(unescaped), unescaped)

    assert part.value == f"@bib{{{escaped}@{escaped}}}"


@pytest.mark.parametrize(  # pyre-ignore[56]
    "type,pages,note,lines",
    [
        (ReferenceType.EDITION, "1", "", tuple()),
        (ReferenceType.COPY, "1", "", tuple()),
        (ReferenceType.PHOTO, "1", "", tuple()),
        (ReferenceType.DISCUSSION, "1", "notes not allowed", tuple()),
        (ReferenceType.DISCUSSION, "1", "", ("1", "2")),
    ],
)
def test_invalid_reference(type, pages, note, lines) -> None:
    with (pytest.raises(ValueError)):
        BibliographyPart(Reference(BIBLIOGRAPHY_ID, type, pages, note, lines))
