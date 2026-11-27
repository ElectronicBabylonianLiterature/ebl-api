from typing import Callable

import attr
import dictdiffer
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.chapter_changelog import dump_chapter_document
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_annotation_kind import AnnotationKind, InvalidAnnotation
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, dump_alignment
from ebl.tests.corpus.line_alignment_errors import align, change_alignment_token
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    create_new_alignment,
)
from ebl.tests.corpus.lines_edit_support import (
    find_chapter_changelog_entries,
    read_json,
)
from ebl.tests.corpus.reference_save_support import (
    ChapterCopies,
    remove_copy_fields,
)
from ebl.tests.corpus.revision_save_support import (
    SAVE_IDS,
    SAVES_AT_REVISION,
    RequestFactory,
)

VIEWS = pytest.mark.parametrize("view", ["view=outline&", "view=chapter&", ""])
LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))


@pytest.fixture
def assert_saves_like_the_full_path(
    client: testing.TestClient,
    reference_client: testing.TestClient,
    database: Database,
    corpus: Corpus,
    copies: ChapterCopies,
) -> Callable[[Chapter, RequestFactory, str], None]:
    def assert_saves(
        chapter: Chapter, create_request: RequestFactory, view: str
    ) -> None:
        sibling = copies.create_sibling(chapter)
        old_document = dump_chapter_document(corpus.find_chapter(chapter.id_))
        query_string = f"{view}revision=legacy"

        result = post_edit(client, chapter, create_request(chapter), query_string)
        reference_result = post_edit(
            reference_client, sibling, create_request(sibling), query_string
        )
        entry, reference_entry = find_chapter_changelog_entries(database)
        new_document = dump_chapter_document(corpus.find_chapter(chapter.id_))

        assert result.status == falcon.HTTP_OK
        assert reference_result.status == falcon.HTTP_OK
        assert remove_copy_fields(read_json(result)) == remove_copy_fields(
            read_json(reference_result)
        )
        copies.assert_equal(chapter, sibling)
        assert dictdiffer.patch(entry["diff"], old_document) == new_document
        assert dictdiffer.patch(reference_entry["diff"], old_document) == new_document
        assert entry["resource_id"] == list(chapter.id_.to_tuple())
        assert reference_entry["resource_id"] == list(sibling.id_.to_tuple())
        assert new_document != old_document

    return assert_saves


@pytest.fixture
def assert_refuses_like_the_full_path(
    client: testing.TestClient,
    reference_client: testing.TestClient,
    database: Database,
    copies: ChapterCopies,
    assert_nothing_saved: Callable[[], None],
) -> Callable[[Chapter, RequestFactory, str], None]:
    def assert_refuses(
        chapter: Chapter, create_request: RequestFactory, status: str
    ) -> None:
        sibling = copies.create_sibling(chapter)
        query_string = "view=outline&revision=legacy"

        result = post_edit(client, chapter, create_request(chapter), query_string)
        reference_result = post_edit(
            reference_client, sibling, create_request(sibling), query_string
        )

        assert result.status == status
        assert reference_result.status == status
        assert read_json(result) == read_json(reference_result)
        copies.assert_equal(chapter, sibling)
        assert_nothing_saved()

    return assert_refuses


@VIEWS
@pytest.mark.parametrize("create_request", SAVES_AT_REVISION, ids=SAVE_IDS)
def test_save_at_a_revision_equals_the_save_of_the_full_path(
    move_chapter: Chapter,
    assert_saves_like_the_full_path: Callable[[Chapter, RequestFactory, str], None],
    create_request: RequestFactory,
    view: str,
) -> None:
    assert_saves_like_the_full_path(move_chapter, create_request, view)


@VIEWS
@LINES
def test_line_annotation_equals_the_annotation_of_the_full_path(
    annotation_chapter: Chapter,
    assert_saves_like_the_full_path: Callable[[Chapter, RequestFactory, str], None],
    annotation_kind: AnnotationKind,
    index: int,
    view: str,
) -> None:
    assert_saves_like_the_full_path(
        annotation_chapter,
        lambda chapter: annotation_kind.create_new_request(chapter, index),
        view,
    )


def test_invalid_annotation_is_refused_like_on_the_full_path(
    annotation_chapter: Chapter,
    assert_refuses_like_the_full_path: Callable[[Chapter, RequestFactory, str], None],
    invalid_annotation: InvalidAnnotation,
) -> None:
    assert_refuses_like_the_full_path(
        annotation_chapter,
        invalid_annotation.create_request,
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    )


@pytest.mark.parametrize("number", [ANNOTATION_LINE_COUNT, -1, 10**20])
def test_line_position_out_of_range_is_refused_like_on_the_full_path(
    annotation_chapter: Chapter,
    assert_refuses_like_the_full_path: Callable[[Chapter, RequestFactory, str], None],
    annotation_kind: AnnotationKind,
    number: int,
) -> None:
    assert_refuses_like_the_full_path(
        annotation_chapter,
        lambda chapter: annotation_kind.create_request(
            number, annotation_kind.dump_new(chapter.lines[0])
        ),
        falcon.HTTP_UNPROCESSABLE_ENTITY,
    )


@LINES
def test_duplicate_alignment_indices_are_refused_like_on_the_full_path(
    annotation_chapter: Chapter,
    assert_refuses_like_the_full_path: Callable[[Chapter, RequestFactory, str], None],
    index: int,
) -> None:
    def create_request(chapter: Chapter) -> ChapterEditRequest:
        alignment = create_new_alignment(chapter.lines[index])
        return ALIGNMENT.create_request(
            index, dump_alignment(change_alignment_token(1, align(3))(alignment))
        )

    assert_refuses_like_the_full_path(
        annotation_chapter, create_request, falcon.HTTP_UNPROCESSABLE_ENTITY
    )


def test_unknown_chapter_is_not_found_like_on_the_full_path(
    client: testing.TestClient,
    reference_client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    missing_chapter = attr.evolve(
        annotation_chapter, name=f"{annotation_chapter.name} missing"
    )

    result, reference_result = (
        annotation_kind.post_new(http_client, missing_chapter, 0)
        for http_client in (client, reference_client)
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert read_json(result) == read_json(reference_result)
