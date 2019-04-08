from ebl.corpus.text import (
    Text, Chapter, Manuscript, Classification, Stage, Period, Provenance,
    ManuscriptType
)
from ebl.tests.factories.bibliography import ReferenceFactory

CATEGORY = 1
INDEX = 2
NAME = 'Paln & Vine'
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
NAME = 'IIc'
ORDER = 1
SIGLUM = 'UrHel3'
MUSEUM_NUMBER = 'BM.x'
ACCESSION = 'K.x'
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY
REFERENCES = (ReferenceFactory.build(), )


TEXT = Text(CATEGORY, INDEX, NAME, VERSES, APPROXIMATE, (
    Chapter(CLASSIFICATION, STAGE, NAME, ORDER, (
        Manuscript(
            SIGLUM,
            MUSEUM_NUMBER,
            ACCESSION,
            PERIOD,
            PROVENANCE,
            TYPE,
            REFERENCES
        ),
    )),
))


def test_constructor_sets_correct_fields():
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.number_of_verses == VERSES
    assert TEXT.approximate_verses == APPROXIMATE
    assert TEXT.chapters[0].classification == CLASSIFICATION
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].name == NAME
    assert TEXT.chapters[0].order == ORDER
    assert TEXT.chapters[0].manuscripts[0].siglum == SIGLUM
    assert TEXT.chapters[0].manuscripts[0].museum_number == MUSEUM_NUMBER
    assert TEXT.chapters[0].manuscripts[0].accession == ACCESSION
    assert TEXT.chapters[0].manuscripts[0].period == PERIOD
    assert TEXT.chapters[0].manuscripts[0].provenance == PROVENANCE
    assert TEXT.chapters[0].manuscripts[0].type == TYPE
    assert TEXT.chapters[0].manuscripts[0].references == REFERENCES


def test_serializing_to_dict():
    # pylint: disable=E1101
    assert TEXT.to_dict() == {
        'category': CATEGORY,
        'index': INDEX,
        'name': NAME,
        'numberOfVerses': VERSES,
        'approximateVerses': APPROXIMATE,
        'chapters': [
            {
                'classification': CLASSIFICATION.value,
                'stage': STAGE.long_name,
                'name': NAME,
                'order': ORDER,
                'manuscripts': [
                    {
                        'siglum': SIGLUM,
                        'museumNumber': MUSEUM_NUMBER,
                        'accession': ACCESSION,
                        'period': PERIOD.long_name,
                        'provenance': PROVENANCE.long_name,
                        'type': TYPE.long_name,
                        'references': [
                            reference.to_dict()
                            for reference in REFERENCES
                        ]
                    }
                ]
            }
        ]
    }


def test_serializing_to_dict_with_documents():
    # pylint: disable=E1101
    assert TEXT.to_dict(True) == {
        'category': CATEGORY,
        'index': INDEX,
        'name': NAME,
        'numberOfVerses': VERSES,
        'approximateVerses': APPROXIMATE,
        'chapters': [
            {
                'classification': CLASSIFICATION.value,
                'stage': STAGE.long_name,
                'name': NAME,
                'order': ORDER,
                'manuscripts': [
                    {
                        'siglum': SIGLUM,
                        'museumNumber': MUSEUM_NUMBER,
                        'accession': ACCESSION,
                        'period': PERIOD.long_name,
                        'provenance': PROVENANCE.long_name,
                        'type': TYPE.long_name,
                        'references': [
                            reference.to_dict(True)
                            for reference in REFERENCES
                        ]
                    }
                ]
            }
        ]
    }
