from ebl.bibliography.reference import (
    BibliographyId, ReferenceType, Reference
)
from ebl.text.line import LineNumber


ID = BibliographyId('id')
TYPE = ReferenceType.EDITION
PAGES = '1-6'
NOTES = 'some notes'
LINES_CITED = (LineNumber('1.'), LineNumber('2a.2.'))
REFERENCE = Reference(ID, TYPE, PAGES, NOTES, LINES_CITED)


SERIALIZED_REFERENCE = {
    'id': ID,
    'type': TYPE,
    'pages': PAGES,
    'notes': NOTES,
    'lines_cited': [line_number for line_number in LINES_CITED]
}


def test_reference():
    assert REFERENCE.id == ID
    assert REFERENCE.type == TYPE
    assert REFERENCE.pages == PAGES
    assert REFERENCE.notes == NOTES
    assert REFERENCE.lines_cited == LINES_CITED


def test_defaults():
    reference = Reference(ID, TYPE)

    assert reference.pages == ''
    assert reference.notes == ''
    assert reference.lines_cited == tuple()


def test_to_dict():
    assert REFERENCE.to_dict() == SERIALIZED_REFERENCE


def test_from_dict():
    reference = Reference.from_dict(SERIALIZED_REFERENCE)

    assert reference == REFERENCE
