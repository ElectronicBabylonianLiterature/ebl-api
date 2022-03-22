from pymongo.database import Database
import pytest
from ebl.corpus.application.schemas import ChapterSchema
from ebl.errors import NotFoundError

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.corpus import ChapterFactory, TextIdFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import ChapterName
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.infrastructure.parallel_lines import MongoParallelRepository

MUSEUM_NUMBER: MuseumNumber = MuseumNumber("X", "1")
TEXT_ID: TextId = TextIdFactory.build()
CHAPTER_NAME: ChapterName = ChapterName(Stage.OLD_ASSYRIAN, "new and improved", "I")


@pytest.fixture
def repository(database: Database) -> MongoParallelRepository:
    return MongoParallelRepository(database)


def test_fragment_exists_true(
    database: Database, repository: MongoParallelRepository
) -> None:
    fragment = FragmentFactory.build(number=MUSEUM_NUMBER)
    database["fragments"].insert_one(FragmentSchema().dump(fragment))

    assert repository.fragment_exists(MUSEUM_NUMBER) is True


def test_fragment_exists_false(repository: MongoParallelRepository) -> None:
    assert repository.fragment_exists(MUSEUM_NUMBER) is False


def test_chapter_exists_true(
    database: Database, repository: MongoParallelRepository
) -> None:
    chapter = ChapterFactory.build(
        text_id=TEXT_ID,
        stage=CHAPTER_NAME.stage,
        name=CHAPTER_NAME.name,
    )
    database["chapters"].insert_one(ChapterSchema().dump(chapter))

    assert repository.chapter_exists(TEXT_ID, CHAPTER_NAME) is True


def test_chapter_exists_false(repository: MongoParallelRepository) -> None:
    assert repository.chapter_exists(TEXT_ID, CHAPTER_NAME) is False


def test_find_implicit_chapter(
    database: Database, repository: MongoParallelRepository
) -> None:
    chapter = ChapterFactory.build(text_id=TEXT_ID)
    database["chapters"].insert_one(ChapterSchema().dump(chapter))

    assert repository.find_implicit_chapter(TEXT_ID) == ChapterName(
        chapter.stage, chapter.version, chapter.name
    )


def test_find_implicit_chapter_not_found(repository: MongoParallelRepository) -> None:
    with pytest.raises(NotFoundError):
        repository.find_implicit_chapter(TEXT_ID)
