import pytest
from ebl.corpus.text import (
    Text, Chapter, Manuscript, Classification, Stage, PeriodModifier, Period,
    Provenance, ManuscriptType, TextId
)
from ebl.tests.factories.bibliography import ReferenceFactory

CATEGORY = 1
INDEX = 2
NAME = 'Palm & Vine'
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = 'A'
NAME = 'IIc'
ORDER = 1
SIGLUM_DISAMBIGUATOR = '1c'
MUSEUM_NUMBER = 'BM.x'
ACCESSION = ''
PERIOD_MODIFIER = PeriodModifier.LATE
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY
NOTES = 'some notes'
REFERENCES = (ReferenceFactory.build(), )


TEXT = Text(CATEGORY, INDEX, NAME, VERSES, APPROXIMATE, (
    Chapter(CLASSIFICATION, STAGE, VERSION, NAME, ORDER, (
        Manuscript(
            SIGLUM_DISAMBIGUATOR,
            MUSEUM_NUMBER,
            ACCESSION,
            PERIOD_MODIFIER,
            PERIOD,
            PROVENANCE,
            TYPE,
            NOTES,
            REFERENCES
        ),
    )),
))


def test_constructor_sets_correct_fields():
    assert TEXT.id == TextId(CATEGORY, INDEX)
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.number_of_verses == VERSES
    assert TEXT.approximate_verses == APPROXIMATE
    assert TEXT.chapters[0].classification == CLASSIFICATION
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].version == VERSION
    assert TEXT.chapters[0].name == NAME
    assert TEXT.chapters[0].order == ORDER
    assert TEXT.chapters[0].manuscripts[0].siglum == (
        PROVENANCE,
        PERIOD,
        TYPE,
        SIGLUM_DISAMBIGUATOR
    )

    assert TEXT.chapters[0].manuscripts[0].siglum_disambiguator ==\
        SIGLUM_DISAMBIGUATOR
    assert TEXT.chapters[0].manuscripts[0].museum_number == MUSEUM_NUMBER
    assert TEXT.chapters[0].manuscripts[0].accession == ACCESSION
    assert TEXT.chapters[0].manuscripts[0].period_modifier == PERIOD_MODIFIER
    assert TEXT.chapters[0].manuscripts[0].period == PERIOD
    assert TEXT.chapters[0].manuscripts[0].provenance == PROVENANCE
    assert TEXT.chapters[0].manuscripts[0].type == TYPE
    assert TEXT.chapters[0].manuscripts[0].notes == NOTES
    assert TEXT.chapters[0].manuscripts[0].references == REFERENCES


def test_giving_museum_number_and_accession_is_invalid():
    with pytest.raises(ValueError):
        Manuscript(
            museum_number='when museam number if given',
            accession='then accession not allowed'
        )


def test_duplicate_sigla_are_invalid():
    with pytest.raises(ValueError):
        Chapter(manuscripts=(
            Manuscript(
                siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                period=PERIOD,
                provenance=PROVENANCE,
                type=TYPE
            ),
            Manuscript(
                siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                period=PERIOD,
                provenance=PROVENANCE,
                type=TYPE
            ),
        ))


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
                'stage': STAGE.value,
                'version': VERSION,
                'name': NAME,
                'order': ORDER,
                'manuscripts': [
                    {
                        'siglumDisambiguator': SIGLUM_DISAMBIGUATOR,
                        'museumNumber': MUSEUM_NUMBER,
                        'accession': ACCESSION,
                        'periodModifier': PERIOD_MODIFIER.value,
                        'period': PERIOD.value,
                        'provenance': PROVENANCE.long_name,
                        'type': TYPE.long_name,
                        'notes': NOTES,
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
                'stage': STAGE.value,
                'version': VERSION,
                'name': NAME,
                'order': ORDER,
                'manuscripts': [
                    {
                        'siglumDisambiguator': SIGLUM_DISAMBIGUATOR,
                        'museumNumber': MUSEUM_NUMBER,
                        'accession': ACCESSION,
                        'periodModifier': PERIOD_MODIFIER.value,
                        'period': PERIOD.value,
                        'provenance': PROVENANCE.long_name,
                        'type': TYPE.long_name,
                        'notes': NOTES,
                        'references': [
                            reference.to_dict(True)
                            for reference in REFERENCES
                        ]
                    }
                ]
            }
        ]
    }


def test_stage():
    periods = [period.value for period in Period]
    stages = [stage.value for stage in Stage]
    assert stages == [*periods, 'Standard Babylonian']
