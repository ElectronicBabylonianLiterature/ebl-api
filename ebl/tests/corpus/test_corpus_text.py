from ebl.corpus.text import Text, Chapter, Classification, Stage


CATEGORY = 1
INDEX = 2
NAME = 'Paln & Vine'
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
NUMBER = 1
TEXT = Text(CATEGORY, INDEX, NAME, (
    Chapter(CLASSIFICATION, STAGE, NUMBER),
))


def test_text():
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.chapters[0].classification == CLASSIFICATION
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].number == NUMBER


def test_to_dict():
    assert TEXT.to_dict() == {
        'category': CATEGORY,
        'index': INDEX,
        'name': NAME,
        'chapters': [
            {
                'classification': CLASSIFICATION.value,
                'stage': STAGE.long_name,  # pylint: disable=E1101
                'number': 1
            }
        ]
    }
