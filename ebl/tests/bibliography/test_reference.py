from ebl.bibliography.domain.reference import (BibliographyId, Reference,
                                               ReferenceType)

ID = BibliographyId('RN.1')
TYPE = ReferenceType.EDITION
PAGES = '1-6'
NOTES = 'some notes'
LINES_CITED = ('o. 1', 'r. iii! 2a.2', "9'")

REFERENCE = Reference(ID, TYPE, PAGES, NOTES, LINES_CITED)

SERIALIZED_REFERENCE = {
    'id': ID,
    'type': TYPE.name,
    'pages': PAGES,
    'notes': NOTES,
    'linesCited': list(LINES_CITED)
}


def create_reference_with_document(bibliography_entry):
    return Reference(
        bibliography_entry['id'],
        TYPE,
        PAGES,
        NOTES,
        LINES_CITED,
        bibliography_entry
    )


def test_reference(bibliography_entry):
    reference_with_document =\
        create_reference_with_document(bibliography_entry)

    assert reference_with_document.id == bibliography_entry['id']
    assert reference_with_document.type == TYPE
    assert reference_with_document.pages == PAGES
    assert reference_with_document.notes == NOTES
    assert reference_with_document.lines_cited == LINES_CITED
    assert reference_with_document.document == bibliography_entry


def test_defaults():
    reference = Reference(ID, TYPE)

    assert reference.pages == ''
    assert reference.notes == ''
    assert reference.lines_cited == tuple()
    assert reference.document is None


def test_to_dict(bibliography_entry):
    reference_with_document =\
        create_reference_with_document(bibliography_entry)

    assert reference_with_document.to_dict() == {
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id
    }


def test_to_dict_with_document(bibliography_entry):
    reference_with_document =\
        create_reference_with_document(bibliography_entry)

    assert reference_with_document.to_dict(True) == {
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id,
        'document': bibliography_entry
    }


def test_from_dict():
    result = Reference.from_dict(SERIALIZED_REFERENCE)

    assert result == REFERENCE


def test_from_dict_with_document(bibliography_entry):
    reference_with_document =\
        create_reference_with_document(bibliography_entry)

    result = Reference.from_dict({
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id,
        'document': bibliography_entry
    })

    assert result == reference_with_document
