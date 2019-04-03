from ebl.corpus.text import (
    Text, Chapter, Manuscript, Classification, Stage, Period, Provenance,
    ManuscriptType
)


CATEGORY = 1
INDEX = 2
NAME = 'Paln & Vine'
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
NUMBER = 1
SIGLUM = 'UrHel3'
MUSEUM_NUMBER = 'BM.x'
ACCESSION = 'K.x'
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY


TEXT = Text(CATEGORY, INDEX, NAME, (
    Chapter(CLASSIFICATION, STAGE, NUMBER, (
        Manuscript(
            SIGLUM,
            MUSEUM_NUMBER,
            ACCESSION,
            PERIOD,
            PROVENANCE,
            TYPE
        ),
    )),
))


def test_constructor_sets_correct_fields():
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.chapters[0].classification == CLASSIFICATION
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].number == NUMBER
    assert TEXT.chapters[0].manuscripts[0].siglum == SIGLUM
    assert TEXT.chapters[0].manuscripts[0].museum_number == MUSEUM_NUMBER
    assert TEXT.chapters[0].manuscripts[0].accession == ACCESSION
    assert TEXT.chapters[0].manuscripts[0].period == PERIOD
    assert TEXT.chapters[0].manuscripts[0].provenance == PROVENANCE
    assert TEXT.chapters[0].manuscripts[0].type == TYPE


def test_serializing_to_dict():
    # pylint: disable=E1101
    assert TEXT.to_dict() == {
        'category': CATEGORY,
        'index': INDEX,
        'name': NAME,
        'chapters': [
            {
                'classification': CLASSIFICATION.value,
                'stage': STAGE.long_name,
                'number': 1,
                'manuscripts': [
                    {
                        'siglum': SIGLUM,
                        'museumNumber': MUSEUM_NUMBER,
                        'accession': ACCESSION,
                        'period': PERIOD.long_name,
                        'provenance': PROVENANCE.long_name,
                        'type': TYPE.long_name
                    }
                ]
            }
        ]
    }
