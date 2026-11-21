import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_annotation_kind import ANNOTATION_QUERY, AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, LEMMATIZATION
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    SPECIAL_INDEX,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    read_json,
)
from ebl.tests.corpus.outline_support import dump_outline
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)

DEFAULT_VIEW_QUERY = "revision=legacy"
CHAPTER_VIEW_QUERY = "view=chapter&revision=legacy"
CHAPTER_VIEW_QUERIES = (DEFAULT_VIEW_QUERY, CHAPTER_VIEW_QUERY)
LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))


def test_outline_view_is_the_outline_with_the_new_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    result = annotation_kind.post_new(client, annotation_chapter, 0)
    revision = text_repository.find_chapter_revision(annotation_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(annotation_chapter, revision)
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize(
    "index,query_string",
    [
        *((index, DEFAULT_VIEW_QUERY) for index in range(ANNOTATION_LINE_COUNT)),
        (0, CHAPTER_VIEW_QUERY),
    ],
)
def test_chapter_view_is_the_annotated_chapter(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    index: int,
    query_string: str,
) -> None:
    expected = annotation_kind.update_chapter(annotation_chapter, index)

    result = annotation_kind.post_new(client, annotation_chapter, index, query_string)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(expected)
    assert result.json != create_chapter_dto(annotation_chapter)
    assert "revision" not in read_json(result)


def test_chapter_route_returns_the_annotated_chapter(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    expected = annotation_kind.update_chapter(annotation_chapter, SPECIAL_INDEX)
    annotation_kind.post_new(client, annotation_chapter, SPECIAL_INDEX)

    result = simulate_get(client, create_chapter_url(annotation_chapter))

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(expected)


def test_outline_view_equals_the_outline_route_after_the_save(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    result = annotation_kind.post_new(client, annotation_chapter, 0)
    outline_result = simulate_get(
        client, create_chapter_url(annotation_chapter, "/outline")
    )

    assert outline_result.status == falcon.HTTP_OK
    assert outline_result.json == result.json


@pytest.mark.parametrize("index", [0, SPECIAL_INDEX])
def test_lemmatizing_with_the_revision_of_the_alignment_save(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    index: int,
) -> None:
    aligned_chapter = ALIGNMENT.update_chapter(annotation_chapter, index)
    first_result = ALIGNMENT.post_new(client, annotation_chapter, index)
    first_revision = read_json(first_result)["revision"]

    second_result = LEMMATIZATION.post_new(
        client, annotation_chapter, index, f"view=outline&revision={first_revision}"
    )
    found = text_repository.find_chapter(annotation_chapter.id_)

    assert second_result.status == falcon.HTTP_OK
    assert read_json(second_result)["revision"] != first_revision
    assert found.lines == LEMMATIZATION.update_chapter(aligned_chapter, index).lines
    assert found.lines != aligned_chapter.lines
    assert count_chapter_changelog_entries(database) == 2


@pytest.mark.parametrize("query_string", [ANNOTATION_QUERY, *CHAPTER_VIEW_QUERIES])
def test_save_writes_one_changelog_entry(
    client: testing.TestClient,
    database: Database,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    query_string: str,
) -> None:
    result = annotation_kind.post_new(client, annotation_chapter, 0, query_string)

    assert result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1


@LINES
def test_saving_the_stored_annotation_keeps_the_lines(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    index: int,
) -> None:
    request = annotation_kind.create_stored_request(annotation_chapter, index)

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)

    assert result.status == falcon.HTTP_OK
    assert (
        text_repository.find_chapter(annotation_chapter.id_).lines
        == annotation_chapter.lines
    )
