from pymongo.database import Database
import pytest
from ebl.corpus.application.schemas import ChapterSchema
from ebl.errors import NotFoundError

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.corpus import ChapterFactory, TextIdFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import ChapterName
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.infrastructure.mongo_parallel_repository import (
    MongoParallelRepository,
)

FRAGMENTS_COLLECTION = "fragments"
CHAPTERS_COLLECTION = "chapters"
MUSEUM_NUMBER = MuseumNumber("X", "1")
TEXT_ID: TextId = TextIdFactory.build()
CHAPTER_NAME = ChapterName(Stage.OLD_ASSYRIAN, "new and improved", "I")


def test_fragment_exists_true(
    database: Database, parallel_repository: MongoParallelRepository
) -> None:
    fragment = FragmentFactory.build(number=MUSEUM_NUMBER)
    database[FRAGMENTS_COLLECTION].insert_one(FragmentSchema().dump(fragment))

    assert parallel_repository.fragment_exists(MUSEUM_NUMBER) is True


def test_fragment_exists_false(parallel_repository: MongoParallelRepository) -> None:
    assert parallel_repository.fragment_exists(MUSEUM_NUMBER) is False


def test_chapter_exists_true(
    database: Database, parallel_repository: MongoParallelRepository
) -> None:
    chapter = ChapterFactory.build(
        text_id=TEXT_ID,
        stage=CHAPTER_NAME.stage,
        name=CHAPTER_NAME.name,
    )
    database[CHAPTERS_COLLECTION].insert_one(ChapterSchema().dump(chapter))

    assert parallel_repository.chapter_exists(TEXT_ID, CHAPTER_NAME) is True


def test_chapter_exists_false(parallel_repository: MongoParallelRepository) -> None:
    assert parallel_repository.chapter_exists(TEXT_ID, CHAPTER_NAME) is False


def test_find_implicit_chapter(
    database: Database, parallel_repository: MongoParallelRepository
) -> None:
    chapter = ChapterFactory.build(text_id=TEXT_ID)
    database[CHAPTERS_COLLECTION].insert_one(ChapterSchema().dump(chapter))

    assert parallel_repository.find_implicit_chapter(TEXT_ID) == ChapterName(
        chapter.stage, chapter.version, chapter.name
    )


def test_find_implicit_chapter_not_found(
    parallel_repository: MongoParallelRepository,
) -> None:
    with pytest.raises(NotFoundError):
        parallel_repository.find_implicit_chapter(TEXT_ID)
