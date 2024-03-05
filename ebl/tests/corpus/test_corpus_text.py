from ebl.corpus.domain.chapter import Classification, make_title
from ebl.common.domain.stage import Stage
from ebl.corpus.domain.text import ChapterListing, Text, UncertainFragment
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import TranslationLine

GENRE = Genre.LITERATURE
CATEGORY = 1
INDEX = 2
NAME = "Palm & Vine"
HAS_DOI = True
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
INTRO = "**Intro**"
CHAPTER_NAME = "I"
TRANSLATION = (
    TranslationLine([StringPart("not the title")], "de"),
    TranslationLine([StringPart("the title,")], "en"),
)
UNCERTAIN_FRAGMENTS = (UncertainFragment(MuseumNumber("X", "1")),)
CHAPTER = ChapterListing(STAGE, CHAPTER_NAME, TRANSLATION, UNCERTAIN_FRAGMENTS)


TEXT = Text(
    GENRE, CATEGORY, INDEX, NAME, HAS_DOI, VERSES, APPROXIMATE, INTRO, (CHAPTER,)
)


def test_text_constructor_sets_correct_fields() -> None:
    assert TEXT.id == TextId(GENRE, CATEGORY, INDEX)
    assert TEXT.genre == GENRE
    assert TEXT.category == CATEGORY
    assert TEXT.index == INDEX
    assert TEXT.name == NAME
    assert TEXT.has_doi == HAS_DOI
    assert TEXT.number_of_verses == VERSES
    assert TEXT.approximate_verses == APPROXIMATE
    assert TEXT.intro == INTRO
    assert TEXT.chapters[0].stage == STAGE
    assert TEXT.chapters[0].name == CHAPTER_NAME
    assert TEXT.chapters[0].translation == TRANSLATION
    assert TEXT.chapters[0].uncertain_fragments == UNCERTAIN_FRAGMENTS


def test_title() -> None:
    assert CHAPTER.title == make_title(TRANSLATION)
