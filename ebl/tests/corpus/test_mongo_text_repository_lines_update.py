import re
from typing import Callable, Mapping

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.schemas import LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line import Line
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.errors import ConflictError, NotFoundError
from ebl.tests.corpus.chapter_change_support import FIRST_EDITED_NUMBER, edit_line
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    create_annotation_chapter,
    replace_item,
)
from ebl.tests.corpus.lines_edit_support import STALE_REVISION, find_stored_chapter
from ebl.tests.corpus.outline_support import remove_key
from ebl.tests.transliteration.storage_test_helpers import stored_dump

LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))
NO_SERVER_POSITIONS = (-1, -ANNOTATION_LINE_COUNT, 2**31, 10**20)
NO_POSITIONS = pytest.mark.parametrize(
    "index", [ANNOTATION_LINE_COUNT, 2**31 - 1, *NO_SERVER_POSITIONS]
)
BROKEN_INDEX = 3


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_annotation_chapter())


def edit(chapter: Chapter, index: int) -> Line:
    return edit_line(chapter.lines[index], FIRST_EDITED_NUMBER)


@LINES
def test_lines_update_sets_the_line_and_the_revision(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    index: int,
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)
    line = edit(chapter, index)

    revision = text_repository.update_lines_at_revision(
        chapter.id_, {index: line}, LEGACY_REVISION
    )

    assert find_stored_chapter(database, chapter) == {
        **stored_chapter,
        "lines": list(
            replace_item(
                stored_chapter["lines"], index, stored_dump(LineSchema(), line)
            )
        ),
        REVISION_FIELD: revision,
    }
    assert revision == text_repository.find_chapter_revision(chapter.id_)
    assert revision != LEGACY_REVISION


def test_lines_update_without_lines_sets_the_revision(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    revision = text_repository.update_lines_at_revision(
        chapter.id_, {}, LEGACY_REVISION
    )

    assert find_stored_chapter(database, chapter) == {
        **stored_chapter,
        REVISION_FIELD: revision,
    }


def test_lines_update_at_the_revision_of_the_previous_update(
    text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    lines = [edit(chapter, index) for index in (0, 1)]
    first_revision = text_repository.update_lines_at_revision(
        chapter.id_, {0: lines[0]}, LEGACY_REVISION
    )

    second_revision = text_repository.update_lines_at_revision(
        chapter.id_,
        {1: attr.evolve(lines[1], number=chapter.lines[1].number)},
        first_revision,
    )

    assert second_revision == text_repository.find_chapter_revision(chapter.id_)
    assert second_revision != first_revision
    assert text_repository.find_chapter(chapter.id_).lines[0] == lines[0]


@pytest.mark.parametrize("stale_revision", [STALE_REVISION, LEGACY_REVISION])
def test_lines_update_at_a_stale_revision(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    stale_revision: str,
) -> None:
    text_repository.update(chapter.id_, chapter)
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(ConflictError, match=f"expected revision {stale_revision}"):
        text_repository.update_lines_at_revision(
            chapter.id_, {0: edit(chapter, 0)}, stale_revision
        )

    assert find_stored_chapter(database, chapter) == stored_chapter


def test_lines_update_confirms_an_update_whose_reply_was_lost(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update_one = text_repository._chapters.update_one
    line = edit(chapter, 0)

    def update_and_lose_the_reply(query: Mapping[str, object], update: object) -> None:
        update_one(query, update)
        raise NotFoundError("chapter not found.")

    monkeypatch.setattr(
        text_repository._chapters, "update_one", update_and_lose_the_reply
    )

    revision = text_repository.update_lines_at_revision(
        chapter.id_, {0: line}, LEGACY_REVISION
    )

    assert revision == find_stored_chapter(database, chapter)[REVISION_FIELD]
    assert text_repository.find_chapter(chapter.id_).lines[0] == line


@pytest.mark.parametrize(
    "use_line",
    [
        lambda repository, id_: repository.find_line_with_revision(id_, 0),
        lambda repository, id_: repository.update_lines_at_revision(
            id_, {}, LEGACY_REVISION
        ),
        lambda repository, id_: repository.update_lines_at_revision(
            id_, {}, STALE_REVISION
        ),
    ],
)
def test_line_of_an_unknown_chapter(
    database: Database,
    text_repository: MongoTextRepository,
    chapter: Chapter,
    use_line: Callable[[MongoTextRepository, object], object],
) -> None:
    missing_id = attr.evolve(chapter.id_, name=f"{chapter.name} missing")
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(NotFoundError, match=re.escape(f"Chapter {missing_id} not")):
        use_line(text_repository, missing_id)

    assert remove_key(find_stored_chapter(database, chapter), "_id") == remove_key(
        stored_chapter, "_id"
    )
