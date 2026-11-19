from typing import List, Mapping
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
