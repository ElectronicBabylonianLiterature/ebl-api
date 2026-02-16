from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.tests.factories.bibliography import BibliographyEntryFactory

ID = BibliographyId("RN.1")
TYPE: ReferenceType = ReferenceType.EDITION
PAGES = "1-6"
NOTES = "some notes"
LINES_CITED = ("o. 1", "r. iii! 2a.2", "9'")

REFERENCE = Reference(ID, TYPE, PAGES, NOTES, LINES_CITED)

SERIALIZED_REFERENCE: dict = {
    "id": ID,
    "type": TYPE.name,
    "pages": PAGES,
    "notes": NOTES,
    "linesCited": list(LINES_CITED),
}


def create_reference_with_document(bibliography_entry) -> Reference:
    return Reference(
        bibliography_entry["id"], TYPE, PAGES, NOTES, LINES_CITED, bibliography_entry
    )


def test_reference() -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    reference_with_document = create_reference_with_document(bibliography_entry)

    assert reference_with_document.id == bibliography_entry["id"]
    assert reference_with_document.type == TYPE
    assert reference_with_document.pages == PAGES
    assert reference_with_document.notes == NOTES
    assert reference_with_document.lines_cited == LINES_CITED
    assert reference_with_document.document == bibliography_entry


def test_defaults() -> None:
    reference = Reference(ID, TYPE)

    assert reference.pages == ""
    assert reference.notes == ""
    assert reference.lines_cited == ()
    assert reference.document is None


def test_to_dict() -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    reference_with_document = create_reference_with_document(bibliography_entry)

    assert ReferenceSchema().dump(reference_with_document) == {
        **SERIALIZED_REFERENCE,
        "id": reference_with_document.id,
    }


def test_to_dict_with_document() -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    reference_with_document = create_reference_with_document(bibliography_entry)

    assert ApiReferenceSchema().dump(reference_with_document) == {
        **SERIALIZED_REFERENCE,
        "id": reference_with_document.id,
        "document": bibliography_entry,
    }


def test_from_dict() -> None:
    assert ReferenceSchema().load(SERIALIZED_REFERENCE) == REFERENCE


def test_from_dict_with_document() -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    reference_with_document = create_reference_with_document(bibliography_entry)

    result = ReferenceSchema().load(
        {
            **SERIALIZED_REFERENCE,
            "id": reference_with_document.id,
            "document": bibliography_entry,
        }
    )

    assert result == reference_with_document
