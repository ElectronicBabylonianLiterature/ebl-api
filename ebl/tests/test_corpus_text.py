from ebl.corpus.text import Text, Chapter, Classification, Period


CATEGORY = 1
INDEX = 2
NAME = 'Paln & Vine'
CLASSIFICATION = Classification.ANCIENT
PERIOD = Period.NEO_BABYLONIAN
NUMBER = 1
TOKEN = Text(CATEGORY, INDEX, NAME, (
    Chapter(CLASSIFICATION, PERIOD, NUMBER),
))


def test_text():
    assert TOKEN.category == CATEGORY
    assert TOKEN.index == INDEX
    assert TOKEN.name == NAME
    assert TOKEN.chapters[0].classification == CLASSIFICATION
    assert TOKEN.chapters[0].period == PERIOD
    assert TOKEN.chapters[0].number == NUMBER


def test_to_dict():
    assert TOKEN.to_dict() == {
        'category': CATEGORY,
        'index': INDEX,
        'name': NAME,
        'chapters': [
            {
                'classification': CLASSIFICATION.value,
                'period': PERIOD.long_name,
                'number': 1
            }
        ]
    }
