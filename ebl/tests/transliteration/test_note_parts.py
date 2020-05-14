from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.transliteration.domain.note_line import BibliographyPart


def test_bibliography_part() -> None:
    id_ = BibliographyId("ABC")
    pages = "12-49"
    part = BibliographyPart.of(id_, pages)

    assert part.reference == Reference(id_, ReferenceType.DISCUSSION, pages, "", tuple())
