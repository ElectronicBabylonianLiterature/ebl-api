from typing import Callable, Sequence, Tuple

import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_alignment_errors import align, change_alignment_token
from ebl.tests.corpus.line_annotation_kind import (
    ANNOTATION_QUERY,
    AnnotationKind,
    InvalidAnnotation,
    matches,
)
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, dump_alignment
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    create_new_alignment,
)
from ebl.tests.corpus.lines_edit_support import read_json
from ebl.tests.corpus.revision_save_support import (
    INVALID_REVISION,
    REVISION_REQUIRED,
)

INVALID_POSITION = "Invalid line: {} is not a line position (number of lines: 5)."
LINE_NOT_FOUND = "{} line {} not found."
REFUSED_QUERIES: Sequence[Tuple[str, str]] = (
    ("", REVISION_REQUIRED),
    ("view=outline", REVISION_REQUIRED),
    ("view=chapter", REVISION_REQUIRED),
    ("view=outline&revision=", INVALID_REVISION.format("''")),
    ("revision=a&revision=b", INVALID_REVISION.format("['a', 'b']")),
    ("view=lines&revision=legacy", "unexpected view 'lines'"),
)


def test_invalid_annotation_is_refused(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    invalid_annotation: InvalidAnnotation,
) -> None:
    result = post_edit(
        client,
        annotation_chapter,
        invalid_annotation.create_request(annotation_chapter),
        ANNOTATION_QUERY,
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert matches(invalid_annotation.line_error, read_json(result)["description"])
    assert_nothing_saved()


def test_duplicate_alignment_indices_are_refused(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
) -> None:
    line = annotation_chapter.lines[0]
    alignment = change_alignment_token(1, align(3))(create_new_alignment(line))

    result = post_edit(
        client,
        annotation_chapter,
        ALIGNMENT.create_request(0, dump_alignment(alignment)),
        ANNOTATION_QUERY,
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == (
        f"Invalid line {line.number.atf} {annotation_chapter.manuscripts[0].siglum}. "
        "[3]"
    )
    assert_nothing_saved()


@pytest.mark.parametrize("number", [ANNOTATION_LINE_COUNT, -1, 10**20])
def test_line_position_out_of_range_is_refused(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    number: int,
) -> None:
    request = annotation_kind.create_request(
        number, annotation_kind.dump_new(annotation_chapter.lines[0])
    )

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == INVALID_POSITION.format(number)
    assert_nothing_saved()


@pytest.mark.parametrize("number", ["first", "1.5", "0x1", "move"])
def test_line_position_that_is_not_a_number_is_not_found(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    number: str,
) -> None:
    request = annotation_kind.create_request(
        number, annotation_kind.dump_new(annotation_chapter.lines[0])
    )

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)
    result_without_parameters = post_edit(client, annotation_chapter, request, "")

    assert result.status == falcon.HTTP_NOT_FOUND
    assert read_json(result)["description"] == LINE_NOT_FOUND.format(
        annotation_chapter.id_, number
    )
    assert result_without_parameters.json == result.json
    assert_nothing_saved()


@pytest.mark.parametrize("refused_query", REFUSED_QUERIES)
def test_save_without_a_valid_revision_and_view_is_refused(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    refused_query: Tuple[str, str],
) -> None:
    query_string, description = refused_query

    result = annotation_kind.post_new(client, annotation_chapter, 0, query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == description
    assert_nothing_saved()
