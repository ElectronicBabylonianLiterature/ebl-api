from random import Random
from typing import Sequence

import pytest

from ebl.corpus.application.chapter_changelog import (
    create_change_diff,
    create_chapter_diff,
    dump_chapter_document,
)
from ebl.corpus.application.chapter_changes import change_lines
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.tests.corpus.chapter_change_cases import (
    delete_line,
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
    replay,
)
from ebl.tests.corpus.line_move_support import (
    LONG_LINE_COUNT,
    create_move_chapter,
    find_diff_size,
)
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


@pytest.fixture
def long_chapter() -> Chapter:
    return create_move_chapter(LONG_LINE_COUNT)


@pytest.mark.parametrize("case", CHANGE_CASES, ids=lambda case: case.name)
def test_change_diff_replays_the_change(
    registered_sign_repository: SignRepository, chapter: Chapter, case: ChangeCase
) -> None:
    change = case.create(chapter, registered_sign_repository)

    assert replay(change) == dump_chapter_document(change.new)


@pytest.mark.parametrize("seed", SEEDS)
def test_change_diff_replays_a_random_lines_update(
    registered_sign_repository: SignRepository, seed: int
) -> None:
    chapter = create_move_chapter(RANDOM_LINE_COUNT)
    update = create_random_lines_update(chapter, Random(seed))

    change = change_lines(update, registered_sign_repository, chapter)

    assert replay(change) == dump_chapter_document(change.new)


@pytest.mark.parametrize("seed", SEEDS)
def test_change_diff_replays_a_random_layout(seed: int) -> None:
    change = create_random_layout_change(
        create_move_chapter(RANDOM_LINE_COUNT), Random(seed)
    )

    assert replay(change) == dump_chapter_document(change.new)
    assert change.new != change.old


@pytest.mark.parametrize("kinds", STALE_UPDATES)
def test_change_diff_records_untouched_lines_that_the_update_changes(
    registered_sign_repository: SignRepository, chapter: Chapter, kinds: Sequence[str]
) -> None:
    stale_chapter = make_flags_stale(chapter)
    update = create_lines_update(stale_chapter, kinds, 0)

    change = change_lines(update, registered_sign_repository, stale_chapter)

    assert STALE_INDEX in [edit.position for edit in change.edited]
    assert replay(change) == dump_chapter_document(change.new)
    assert all(
        STALE_INDEX not in range(run.source, run.source + run.count)
        for run in change.unchanged_runs
    )


def test_change_diff_of_an_unchanged_chapter_is_empty(chapter: Chapter) -> None:
    assert create_change_diff(ChapterChange.in_place(chapter, chapter)) == []


def test_entry_of_a_delete_does_not_grow_with_the_lines_behind_it(
    registered_sign_repository: SignRepository, long_chapter: Chapter
) -> None:
    first, last = (
        delete_line(long_chapter, index, registered_sign_repository)
        for index in (0, LONG_LINE_COUNT - 1)
    )
    first_size = find_diff_size(create_change_diff(first))
    last_size = find_diff_size(create_change_diff(last))

    assert abs(first_size - last_size) < last_size / 10
    assert find_diff_size(create_chapter_diff(first.old, first.new)) > 10 * first_size
    assert first.new.parser_version == ATF_PARSER_VERSION


def test_entry_of_an_insert_does_not_grow_with_the_lines_behind_it(
    long_chapter: Chapter,
) -> None:
    first, last = (
        insert_line(long_chapter, position) for position in (0, LONG_LINE_COUNT)
    )
    first_size = find_diff_size(create_change_diff(first))
    last_size = find_diff_size(create_change_diff(last))

    assert abs(first_size - last_size) < last_size / 10
    assert find_diff_size(create_chapter_diff(first.old, first.new)) > 10 * first_size
