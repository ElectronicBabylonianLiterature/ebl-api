from typing import Callable

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_annotation_kind import ANNOTATION_QUERY, AnnotationKind
from ebl.tests.corpus.line_annotation_support import ANNOTATION_LINE_COUNT
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)

VIEW_PREFIXES = ("view=outline&", "")


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_stale_revision_conflicts_and_the_fresh_revision_succeeds(
    client: testing.TestClient,
    database: Database,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    view: str,
) -> None:
    stored_chapter = find_stored_chapter(database, annotation_chapter)
    conflict = chapter_revision_conflict(
        annotation_chapter.id_, STALE_REVISION, LEGACY_REVISION
    )

    stale_result = annotation_kind.post_new(
        client, annotation_chapter, 0, f"{view}revision={STALE_REVISION}"
    )
    chapter_after_conflict = find_stored_chapter(database, annotation_chapter)
    changelog_entries_after_conflict = count_chapter_changelog_entries(database)
    fresh_result = annotation_kind.post_new(
        client, annotation_chapter, 0, f"{view}revision=legacy"
    )

    assert stale_result.status == falcon.HTTP_CONFLICT
    assert read_json(stale_result)["description"] == str(conflict)
    assert chapter_after_conflict == stored_chapter
    assert changelog_entries_after_conflict == 0
    assert fresh_result.status == falcon.HTTP_OK
    assert find_stored_chapter(database, annotation_chapter) != stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_second_save_at_the_same_revision_conflicts(
    client: testing.TestClient,
    database: Database,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    view: str,
) -> None:
    query_string = f"{view}revision=legacy"

    first_result = annotation_kind.post_new(client, annotation_chapter, 0, query_string)
    stored_chapter = find_stored_chapter(database, annotation_chapter)
    second_result = annotation_kind.post_new(
        client, annotation_chapter, 1, query_string
    )

    assert first_result.status == falcon.HTTP_OK
    assert second_result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, annotation_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 1


def test_saving_in_an_updated_chapter_at_the_legacy_revision(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    text_repository.update(annotation_chapter.id_, annotation_chapter)
    stored_chapter = find_stored_chapter(database, annotation_chapter)

    result = annotation_kind.post_new(client, annotation_chapter, 0)

    assert result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, annotation_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 0


def test_stale_revision_is_reported_before_an_invalid_annotation(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    result = post_edit(
        client,
        annotation_chapter,
        annotation_kind.create_request(ANNOTATION_LINE_COUNT, []),
        "revision=stale",
    )

    assert result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_saving_in_an_unknown_chapter(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    revision: str,
) -> None:
    missing_chapter = attr.evolve(
        annotation_chapter, name=f"{annotation_chapter.name} missing"
    )

    result = annotation_kind.post_new(
        client, missing_chapter, 0, f"view=outline&revision={revision}"
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert_nothing_saved()


@pytest.mark.parametrize("query_string", ["", ANNOTATION_QUERY, "revision=legacy"])
def test_saving_requires_write_scope(
    guest_client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    query_string: str,
) -> None:
    result = annotation_kind.post_new(guest_client, annotation_chapter, 0, query_string)

    assert result.status == falcon.HTTP_FORBIDDEN
    assert_nothing_saved()
