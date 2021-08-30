from ebl.corpus.domain.chapter import Classification
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text import ChapterListing, Text, UncertainFragment
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.fragmentarium.domain.museum_number import MuseumNumber

GENRE = Genre.LITERATURE
CATEGORY = 1
INDEX = 2
NAME = "Palm & Vine"
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
INTRO = "**Intro**"
CHAPTER_NAME = "I"
TRANSLATION = tuple()
UNCERTAIN_FRAGMENTS = (UncertainFragment(MuseumNumber("X", "1"), True),)

TEXT = Text(
    GENRE,
    CATEGORY,
    INDEX,
    NAME,
    VERSES,
    APPROXIMATE,
    INTRO,
    (ChapterListing(STAGE, CHAPTER_NAME, TRANSLATION, UNCERTAIN_FRAGMENTS),),
)


def test_text_constructor_sets_correct_fields():
    assert TEXT.id == TextId(GENRE, CATEGORY, INDEX)
    assert TEXT.genre == GENRE
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.number_of_verses == VERSES
    assert TEXT.approximate_verses == APPROXIMATE
    assert TEXT.intro == INTRO
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].name == CHAPTER_NAME
    assert TEXT.chapters[0].translation == TRANSLATION
    assert TEXT.chapters[0].uncertain_fragments == UNCERTAIN_FRAGMENTS
