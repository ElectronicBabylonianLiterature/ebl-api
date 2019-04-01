from ebl.bibliography.reference import (
    ReferenceType, Reference
)
from ebl.text.line import LineNumber


TYPE = ReferenceType.EDITION
PAGES = '1-6'
NOTES = 'some notes'
LINES_CITED = (LineNumber('1.'), LineNumber('2a.2.'))


SERIALIZED_REFERENCE = {
    'type': TYPE.name,
    'pages': PAGES,
    'notes': NOTES,
    'linesCited': [line_number for line_number in LINES_CITED]
}


def test_reference(reference_with_document, bibliography_entry):
    assert reference_with_document.id == bibliography_entry['id']
    assert reference_with_document.type == TYPE
    assert reference_with_document.pages == PAGES
    assert reference_with_document.notes == NOTES
    assert reference_with_document.lines_cited == LINES_CITED
    assert reference_with_document.document == bibliography_entry


def test_defaults():
    reference = Reference('RN01', TYPE)

    assert reference.pages == ''
    assert reference.notes == ''
    assert reference.lines_cited == tuple()
    assert reference.document is None


def test_to_dict(reference_with_document):
    assert reference_with_document.to_dict() == {
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id
    }


def test_to_dict_with_document(reference_with_document, bibliography_entry):
    assert reference_with_document.to_dict(True) == {
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id,
        'document': bibliography_entry
    }


def test_from_dict(reference):
    result = Reference.from_dict({
        **SERIALIZED_REFERENCE,
        'id': reference.id
    })

    assert result == reference


def test_from_dict_with_document(reference_with_document, bibliography_entry):
    result = Reference.from_dict({
        **SERIALIZED_REFERENCE,
        'id': reference_with_document.id,
        'document': bibliography_entry
    })

    assert result == reference_with_document
