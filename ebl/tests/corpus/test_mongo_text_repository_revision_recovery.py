from typing import Callable, List, Mapping
from unittest.mock import Mock

import attr
import pytest
from pymongo.database import Database
from pymongo.errors import AutoReconnect
from pymongo.results import UpdateResult

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.errors import ConflictError
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    find_stored_chapter,
)
from ebl.tests.corpus.outline_support import create_chapter_with_lines
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION

LINE_COUNT = 4


@pytest.fixture
def chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_chapter_with_lines(LINE_COUNT)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.fixture
def matched_counts(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    text_repository: MongoTextRepository,
) -> List[int]:
    raw_collection = database[CHAPTERS_COLLECTION]
    mocked_collection = Mock(wraps=raw_collection)
    matched_counts: List[int] = []

    def update_and_lose_the_first_reply(
        query: Mapping[str, object], update: Mapping[str, object]
    ) -> UpdateResult:
        result = raw_collection.update_one(query, update)
        matched_counts.append(result.matched_count)
        if len(matched_counts) == 1:
            raise AutoReconnect("update outcome unknown")
        return result

    mocked_collection.update_one.side_effect = update_and_lose_the_first_reply
    monkeypatch.setattr(
        text_repository._chapters,
        "_MongoCollection__get_collection",
        lambda: mocked_collection,
    )
    return matched_counts


def test_update_at_revision_confirms_an_update_whose_reply_was_lost(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    matched_counts: List[int],
) -> None:
    updated_chapter = attr.evolve(chapter, lines=chapter.lines[1:])

    revision = text_repository.update_at_revision(
        chapter.id_, updated_chapter, LEGACY_REVISION
    )

    assert matched_counts == [1, 0]
    assert revision == find_stored_chapter(database, chapter)[REVISION_FIELD]
    assert text_repository.find_chapter(chapter.id_).lines == updated_chapter.lines


def test_update_at_stale_revision_conflicts_after_a_lost_reply(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    matched_counts: List[int],
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(ConflictError):
        text_repository.update_at_revision(
            chapter.id_, attr.evolve(chapter, lines=()), STALE_REVISION
        )

    assert matched_counts == [0, 0]
    assert find_stored_chapter(database, chapter) == stored_chapter


def test_null_revision_is_the_legacy_revision(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    database[CHAPTERS_COLLECTION].update_many({}, {"$set": {REVISION_FIELD: None}})

    assert text_repository.find_chapter_revision(chapter.id_) == LEGACY_REVISION

    new_revision = text_repository.update_at_revision(
        chapter.id_, chapter, LEGACY_REVISION
    )

    assert find_stored_chapter(database, chapter)[REVISION_FIELD] == new_revision


@pytest.mark.parametrize(
    "stored_revision",
    [{"$unset": {REVISION_FIELD: ""}}, {"$set": {REVISION_FIELD: None}}],
    ids=["absent", "null"],
)
def test_find_chapter_with_revision_of_a_chapter_at_the_legacy_revision(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    stored_revision: Mapping[str, object],
) -> None:
    database[CHAPTERS_COLLECTION].update_many({}, stored_revision)

    assert text_repository.find_chapter_with_revision(chapter.id_) == (
        text_repository.find_chapter(chapter.id_),
        LEGACY_REVISION,
    )


def test_find_chapter_with_revision_after_an_update(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    updated_chapter = attr.evolve(chapter, lines=chapter.lines[1:])
    revision = text_repository.update_at_revision(
        chapter.id_, updated_chapter, LEGACY_REVISION
    )

    found_chapter, found_revision = text_repository.find_chapter_with_revision(
        chapter.id_
    )

    assert found_chapter == text_repository.find_chapter(chapter.id_)
    assert found_chapter.lines == updated_chapter.lines
    assert found_revision == revision
    assert found_revision == find_stored_chapter(database, chapter)[REVISION_FIELD]


def test_chapter_and_revision_are_read_from_the_same_document(
    text_repository: MongoTextRepository,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = (text_repository.find_chapter(chapter.id_), LEGACY_REVISION)

    def update_after(read: Callable[..., object]) -> Callable[..., object]:
        def read_before_concurrent_update(*args: object, **kwargs: object) -> object:
            result = read(*args, **kwargs)
            text_repository.update(chapter.id_, attr.evolve(chapter, lines=()))
            return result

        return read_before_concurrent_update

    for read_method in ("find_one", "aggregate"):
        monkeypatch.setattr(
            text_repository._chapters,
            read_method,
            update_after(getattr(text_repository._chapters, read_method)),
        )

    assert text_repository.find_chapter_with_revision(chapter.id_) == expected
