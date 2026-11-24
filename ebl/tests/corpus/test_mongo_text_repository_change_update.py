from random import Random
from typing import Callable, List, Mapping, Sequence

import pytest
from pymongo.database import Database

from ebl.corpus.application.chapter_changes import change_lines
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.errors import ConflictError
from ebl.tests.corpus.chapter_change_cases import (
    CHANGE_CASES,
    RANDOM_LINE_COUNT,
    SEEDS,
    ChangeCase,
    create_random_layout_change,
    create_random_lines_update,
)
from ebl.tests.corpus.chapter_change_support import (
    STALE_INDEX,
    STALE_UPDATES,
    create_lines_update,
    insert_line,
    make_flags_stale,
)
from ebl.tests.corpus.line_move_support import LINE_COUNT, create_move_chapter
from ebl.tests.corpus.lines_edit_support import STALE_REVISION, find_stored_chapter
from ebl.tests.corpus.reference_save_support import ChapterCopies
from ebl.transliteration.application.sign_repository import SignRepository

Update = Mapping[str, object]


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_move_chapter())


@pytest.fixture
def long_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_move_chapter(RANDOM_LINE_COUNT))


@pytest.fixture
def updates(
    text_repository: MongoTextRepository, monkeypatch: pytest.MonkeyPatch
) -> List[Sequence[object]]:
    updates: List[Sequence[object]] = []
    update_one = text_repository._chapters.update_one

    def record_update(query: Mapping[str, object], update: object) -> object:
        updates.append((query, update))
        return update_one(query, update)

    monkeypatch.setattr(text_repository._chapters, "update_one", record_update)
    return updates


@pytest.mark.parametrize("case", CHANGE_CASES, ids=lambda case: case.name)
def test_change_is_stored_like_the_full_update(
    registered_sign_repository: SignRepository,
    copies: ChapterCopies,
    chapter: Chapter,
    case: ChangeCase,
) -> None:
    copies.assert_updates_like_the_full_update(
        case.create(chapter, registered_sign_repository)
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_random_lines_update_is_stored_like_the_full_update(
    registered_sign_repository: SignRepository,
    copies: ChapterCopies,
    long_chapter: Chapter,
    seed: int,
) -> None:
    update = create_random_lines_update(long_chapter, Random(seed))

    copies.assert_updates_like_the_full_update(
        change_lines(update, registered_sign_repository, long_chapter)
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_random_layout_is_stored_like_the_full_update(
    copies: ChapterCopies, long_chapter: Chapter, seed: int
) -> None:
    copies.assert_updates_like_the_full_update(
        create_random_layout_change(long_chapter, Random(seed))
    )


@pytest.mark.parametrize("kinds", STALE_UPDATES)
def test_untouched_line_that_the_update_changes_is_stored(
    registered_sign_repository: SignRepository,
    database: Database,
    copies: ChapterCopies,
    store_editable_chapter: Callable[[Chapter], Chapter],
    kinds: Sequence[str],
) -> None:
    stale_chapter = store_editable_chapter(make_flags_stale(create_move_chapter()))
    stale_line = find_stored_chapter(database, stale_chapter)["lines"][STALE_INDEX]
    change = change_lines(
        create_lines_update(stale_chapter, kinds, 0),
        registered_sign_repository,
        stale_chapter,
    )

    copies.assert_updates_like_the_full_update(change)

    assert stale_line not in find_stored_chapter(database, stale_chapter)["lines"]


def test_change_is_stored_with_one_update_at_the_revision(
    copies: ChapterCopies, chapter: Chapter, updates: List[Sequence[object]]
) -> None:
    copies.update(insert_line(chapter, 1))

    ((query, update),) = updates
    assert query == {**chapter_id_query(chapter.id_), REVISION_FIELD: None}
    assert isinstance(update, list)
    assert [list(stage) for stage in update] == [["$set"]]


def test_change_at_a_stale_revision_conflicts_and_stores_nothing(
    database: Database, copies: ChapterCopies, chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(ConflictError):
        copies.update(insert_line(chapter, 1), STALE_REVISION)

    assert find_stored_chapter(database, chapter) == stored_chapter


def test_change_of_a_changed_chapter_conflicts_and_stores_nothing(
    database: Database,
    text_repository: MongoTextRepository,
    copies: ChapterCopies,
    chapter: Chapter,
) -> None:
    change = insert_line(chapter, 1)
    text_repository.update(chapter.id_, chapter)
    stored_chapter = find_stored_chapter(database, chapter)

    with pytest.raises(ConflictError):
        copies.update(change)

    assert find_stored_chapter(database, chapter) == stored_chapter


def test_changes_follow_each_other_at_their_revisions(
    database: Database, copies: ChapterCopies, chapter: Chapter
) -> None:
    sibling = copies.create_sibling(chapter)
    first = insert_line(chapter, LINE_COUNT)
    second = ChapterChange.in_place(first.new, first.new)
    revision = copies.update(first)
    reference_revision = copies.update_fully(sibling, first.new)

    next_revision = copies.update(second, revision)
    copies.update_fully(sibling, second.new, reference_revision)

    assert find_stored_chapter(database, chapter)[REVISION_FIELD] == next_revision
    assert next_revision not in (revision, LEGACY_REVISION)
    copies.assert_equal(chapter, sibling)
