import attr
import pytest

from ebl.corpus.application.line_move_updater import LineMoveUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_move import LineMove
from ebl.errors import DataError
from ebl.tests.corpus.line_move_support import (
    EXTENT_BREAKING_MOVES,
    EXTENT_KEEPING_MOVES,
    MOVE,
    MOVES,
    STORED_PARSER_VERSION,
    assert_lines_are_annotated,
    create_extent_chapter,
    create_move_chapter,
    find_identities,
    move_chapter_line,
    reorder,
)
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION

MOVED_DOWN_SIGNS = "DIŠ UD\nTA MI\nKU ABZ075\nŠU MA\nKU\nABZ075"


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


@pytest.mark.parametrize("move", MOVES)
def test_update_moves_the_line(
    registered_sign_repository: SignRepository, chapter: Chapter, move: LineMove
) -> None:
    updated = LineMoveUpdater(move, registered_sign_repository).update(chapter)

    assert updated == move_chapter_line(chapter, move)
    assert updated != chapter
    assert find_identities(updated.lines) == find_identities(
        reorder(chapter.lines, move)
    )
    assert_lines_are_annotated(updated.lines)


@pytest.mark.parametrize("move", MOVES)
def test_update_sets_the_signs_of_the_new_order(
    registered_sign_repository: SignRepository, chapter: Chapter, move: LineMove
) -> None:
    reordered = attr.evolve(chapter, lines=reorder(chapter.lines, move), signs=())

    updated = LineMoveUpdater(move, registered_sign_repository).update(chapter)

    assert updated.signs == (
        SignsUpdater(registered_sign_repository).update(reordered).signs
    )
    assert updated.signs != chapter.signs


def test_update_joins_the_sign_rows_in_line_order(
    registered_sign_repository: SignRepository, chapter: Chapter
) -> None:
    updated = LineMoveUpdater(MOVE, registered_sign_repository).update(chapter)

    assert updated.signs == (MOVED_DOWN_SIGNS, MOVED_DOWN_SIGNS)


def test_stored_signs_of_the_chapter_are_the_signs_of_its_lines(
    registered_sign_repository: SignRepository, chapter: Chapter
) -> None:
    assert SignsUpdater(registered_sign_repository).update(chapter) == chapter


def test_update_changes_only_lines_and_signs(
    registered_sign_repository: SignRepository, chapter: Chapter
) -> None:
    updated = LineMoveUpdater(LineMove(3, 1), registered_sign_repository).update(
        chapter
    )

    assert attr.evolve(updated, lines=chapter.lines, signs=chapter.signs) == chapter
    assert updated.manuscripts == chapter.manuscripts
    assert updated.parser_version == STORED_PARSER_VERSION
    assert STORED_PARSER_VERSION != ATF_PARSER_VERSION


@pytest.mark.parametrize(
    "move,message",
    [
        (LineMove(4, 0), "from 4 is not a line position (number of lines: 4)."),
        (LineMove(0, 4), "to 4 is not a line position (number of lines: 4)."),
        (LineMove(2, 2), "the line is already at that position."),
    ],
)
def test_update_with_an_invalid_move(
    registered_sign_repository: SignRepository,
    chapter: Chapter,
    move: LineMove,
    message: str,
) -> None:
    with pytest.raises(DataError) as error:
        LineMoveUpdater(move, registered_sign_repository).update(chapter)

    assert str(error.value) == f"Invalid line move: {message}"


@pytest.mark.parametrize("move,message", EXTENT_BREAKING_MOVES)
def test_update_breaking_a_translation_extent(
    registered_sign_repository: SignRepository, move: LineMove, message: str
) -> None:
    with pytest.raises(DataError) as error:
        LineMoveUpdater(move, registered_sign_repository).update(
            create_extent_chapter()
        )

    assert str(error.value) == message


@pytest.mark.parametrize("move", EXTENT_KEEPING_MOVES)
def test_update_keeping_a_translation_extent(
    registered_sign_repository: SignRepository, move: LineMove
) -> None:
    chapter = create_extent_chapter()

    updated = LineMoveUpdater(move, registered_sign_repository).update(chapter)

    assert updated == move_chapter_line(chapter, move)
