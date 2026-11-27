from functools import partial
from typing import Callable, Sequence, Tuple

import pytest

from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.line_snapshot import LineSnapshot
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import (
    ChapterEditRequest,
    create_import_edit,
    create_manuscripts_edit,
)
from ebl.tests.corpus.line_annotation_kinds import ANNOTATION_KINDS
from ebl.tests.corpus.line_move_support import create_move_request
from ebl.tests.corpus.lines_edit_support import (
    EDITED_INDEX,
    LINES_SUFFIX,
    create_body,
    update_chapter,
)
from ebl.tests.corpus.word_instances_requests import create_word_lemma_request
from ebl.tests.corpus.word_instances_support import MOVE_CHAPTER_WORD, NEW_LEMMA

RequestFactory = Callable[[Chapter], ChapterEditRequest]
ChapterRead = Tuple[Chapter, str]
READ_METHOD = "find_chapter_with_revision"
LINE_READ_METHOD = "find_line_with_revision"
ANNOTATED_INDEX = 1
REVISION_REQUIRED = "revision is required"
INVALID_REVISION = "revision must be a non-empty string, got {} instead"
REFUSED_QUERIES: Sequence[Tuple[str, str]] = (
    ("", REVISION_REQUIRED),
    ("view=outline", REVISION_REQUIRED),
    ("view=chapter", REVISION_REQUIRED),
    ("view=outline&revision=", INVALID_REVISION.format("''")),
    ("revision=a&revision=b", INVALID_REVISION.format("['a', 'b']")),
    ("view=lines&revision=legacy", "unexpected view 'lines'"),
)


def create_lines_request(chapter: Chapter) -> ChapterEditRequest:
    return ChapterEditRequest(
        LINES_SUFFIX, create_body(update_chapter(chapter, EDITED_INDEX), EDITED_INDEX)
    )


def create_line_move_request(chapter: Chapter) -> ChapterEditRequest:
    return create_move_request(0, len(chapter.lines) - 1)


def create_word_instances_request(_: Chapter) -> ChapterEditRequest:
    return create_word_lemma_request(MOVE_CHAPTER_WORD, list(NEW_LEMMA))


SAVES_WITHOUT_REVISION: Sequence[RequestFactory] = (
    partial(create_import_edit, step=0),
    partial(create_manuscripts_edit, step=0),
    create_lines_request,
)
SAVES_AT_REVISION: Sequence[RequestFactory] = (
    *SAVES_WITHOUT_REVISION,
    create_line_move_request,
    *(
        partial(kind.create_new_request, index=ANNOTATED_INDEX)
        for kind in ANNOTATION_KINDS
    ),
    create_word_instances_request,
)
SAVE_WITHOUT_REVISION_IDS: Sequence[str] = ("import", "manuscripts", "lines")
SAVE_IDS: Sequence[str] = (
    *SAVE_WITHOUT_REVISION_IDS,
    "move",
    *(kind.name for kind in ANNOTATION_KINDS),
    "instances",
)


def update_after_read(
    patch: pytest.MonkeyPatch,
    text_repository: MongoTextRepository,
    concurrent_chapter: Chapter,
) -> None:
    read = text_repository.find_chapter_with_revision

    def read_before_concurrent_update(id_: ChapterId) -> ChapterRead:
        chapter_read = read(id_)
        text_repository.update(id_, concurrent_chapter)
        return chapter_read

    patch.setattr(text_repository, READ_METHOD, read_before_concurrent_update)


def read_from_lagging_member(
    patch: pytest.MonkeyPatch,
    text_repository: MongoTextRepository,
    lagging_read: ChapterRead,
) -> None:
    chapter, revision = lagging_read
    patch.setattr(text_repository, READ_METHOD, lambda _: lagging_read)
    patch.setattr(
        text_repository,
        LINE_READ_METHOD,
        lambda _, index: LineSnapshot(
            chapter.lines[index], len(chapter.lines), chapter.manuscripts, revision
        ),
    )
