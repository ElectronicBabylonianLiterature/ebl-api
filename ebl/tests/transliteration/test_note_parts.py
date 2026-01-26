import pytest

from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.transliteration.domain.markup import BibliographyPart

BIBLIOGRAPHY_ID = BibliographyId("ABC")


def test_bibliography_part() -> None:
    pages = "12-49"
    part = BibliographyPart.of(BIBLIOGRAPHY_ID, pages)

    assert part.reference == Reference(
        BIBLIOGRAPHY_ID, ReferenceType.DISCUSSION, pages, "", ()
    )


def test_bibliography_part_escape() -> None:
    unescaped = "@{\\}"
    escaped = "\\@\\{\\\\\\}"
    part = BibliographyPart.of(BibliographyId(unescaped), unescaped)

    assert part.value == f"@bib{{{escaped}@{escaped}}}"


@pytest.mark.parametrize(
    "type,pages,note,lines",
    [
        (ReferenceType.EDITION, "1", "", ()),
        (ReferenceType.COPY, "1", "", ()),
        (ReferenceType.PHOTO, "1", "", ()),
        (ReferenceType.DISCUSSION, "1", "notes not allowed", ()),
        (ReferenceType.DISCUSSION, "1", "", ("1", "2")),
    ],
)
def test_invalid_reference(type, pages, note, lines) -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        BibliographyPart(Reference(BIBLIOGRAPHY_ID, type, pages, note, lines))
