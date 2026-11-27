from typing import Callable, List, Mapping, Sequence

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.schemas import LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_outline import (
    aggregate_chapter_outline,
    aggregate_line_snapshot,
)
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    create_annotation_chapter,
)
from ebl.tests.transliteration.storage_test_helpers import stored_dump
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION

LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))
NO_SERVER_POSITIONS = (-1, -ANNOTATION_LINE_COUNT, 2**31, 10**20)
NO_POSITIONS = pytest.mark.parametrize(
    "index", [ANNOTATION_LINE_COUNT, 2**31 - 1, *NO_SERVER_POSITIONS]
)
BROKEN_INDEX = 3


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_annotation_chapter())


@LINES
def test_line_snapshot_is_the_line_with_what_surrounds_it(
    text_repository: MongoTextRepository, chapter: Chapter, index: int
) -> None:
    snapshot = text_repository.find_line_with_revision(chapter.id_, index)

    assert snapshot.line == chapter.lines[index]
    assert snapshot.line_count == ANNOTATION_LINE_COUNT
    assert snapshot.revision == LEGACY_REVISION
    assert [
        (manuscript.id, manuscript.siglum) for manuscript in snapshot.manuscripts
    ] == [(manuscript.id, manuscript.siglum) for manuscript in chapter.manuscripts]
    assert (
        snapshot.manuscripts
        == text_repository.find_line_with_revision(chapter.id_, 0).manuscripts
    )


@NO_POSITIONS
def test_line_snapshot_of_a_position_that_is_not_a_line(
    text_repository: MongoTextRepository, chapter: Chapter, index: int
) -> None:
    snapshot = text_repository.find_line_with_revision(chapter.id_, index)

    assert snapshot.line is None
    assert snapshot.line_count == ANNOTATION_LINE_COUNT
    assert snapshot.revision == LEGACY_REVISION


@LINES
def test_line_snapshot_reads_one_line(index: int) -> None:
    chapter = create_annotation_chapter()
    (match, project) = aggregate_line_snapshot(chapter.id_, index)

    assert match == {"$match": chapter_id_query(chapter.id_)}
    assert project == {
        "$project": {
            "_id": False,
            "total": {"$size": "$lines"},
            "lines": {"$slice": ["$lines", index, 1]},
            "manuscripts": aggregate_chapter_outline(chapter.id_)[1]["$project"][
                "manuscripts"
            ],
            "revision": {"$ifNull": ["$_cacheRevision", LEGACY_REVISION]},
        }
    }


@pytest.mark.parametrize("index", NO_SERVER_POSITIONS)
def test_line_snapshot_reads_no_line_at_a_position_that_is_not_a_line(
    index: int,
) -> None:
    chapter = create_annotation_chapter()
    project = aggregate_line_snapshot(chapter.id_, index)[1]["$project"]

    assert project["lines"] == {"$literal": []}


def test_line_snapshot_loads_only_its_line(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database[CHAPTERS_COLLECTION].update_many(
        {}, {"$set": {f"lines.{BROKEN_INDEX}.variants": "not a line"}}
    )
    loaded: List[object] = []
    load = LineSchema.load

    def record_load(
        schema: LineSchema, data: Sequence[Mapping[str, object]], *, many: bool
    ) -> object:
        loaded.append(data)
        return load(schema, data, many=many)

    monkeypatch.setattr(LineSchema, "load", record_load)

    snapshot = text_repository.find_line_with_revision(chapter.id_, 0)

    assert snapshot.line == chapter.lines[0]
    assert loaded == [[stored_dump(LineSchema(), chapter.lines[0])]]


def test_line_snapshot_carries_the_stored_revision(
    text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    revision = text_repository.update_at_revision(chapter.id_, chapter, LEGACY_REVISION)

    assert text_repository.find_line_with_revision(chapter.id_, 1).revision == revision


def test_line_and_revision_are_read_from_the_same_document(
    text_repository: MongoTextRepository,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aggregate = text_repository._chapters.aggregate

    def read_before_concurrent_update(pipeline: object) -> object:
        result = aggregate(pipeline)
        text_repository.update(chapter.id_, attr.evolve(chapter, lines=()))
        return result

    monkeypatch.setattr(
        text_repository._chapters, "aggregate", read_before_concurrent_update
    )

    snapshot = text_repository.find_line_with_revision(chapter.id_, 0)

    assert snapshot.line == chapter.lines[0]
    assert snapshot.line_count == ANNOTATION_LINE_COUNT
    assert snapshot.revision == LEGACY_REVISION
