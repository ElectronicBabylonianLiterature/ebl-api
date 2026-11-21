from collections import Counter
from typing import Sequence

import pytest

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_move import LineMove
from ebl.tests.corpus.line_move_support import find_identities, reorder
from ebl.tests.factories.corpus import LineFactory

MAX_LINE_COUNT = 5
ALL_MOVES: Sequence[LineMove] = tuple(
    LineMove(source, target)
    for source in range(MAX_LINE_COUNT)
    for target in range(MAX_LINE_COUNT)
    if source != target
)


def create_lines(line_count: int) -> Sequence[Line]:
    return tuple(LineFactory.build_batch(line_count))


@pytest.mark.parametrize("move", ALL_MOVES)
def test_moving_equals_removing_then_inserting(move: LineMove) -> None:
    line_count = max(move.source, move.target) + 1
    for lines in map(create_lines, range(line_count, MAX_LINE_COUNT + 1)):
        moved = move.apply(lines)

        assert find_identities(moved) == find_identities(reorder(lines, move))
        assert len(moved) == len(lines)
        assert Counter(find_identities(moved)) == Counter(find_identities(lines))


@pytest.mark.parametrize("move", ALL_MOVES)
def test_moved_line_is_at_the_target_and_the_others_keep_their_order(
    move: LineMove,
) -> None:
    lines = create_lines(MAX_LINE_COUNT)
    moved_line = lines[move.source]

    moved = move.apply(lines)

    assert moved[move.target] is moved_line
    assert find_identities([line for line in moved if line is not moved_line]) == (
        find_identities([line for line in lines if line is not moved_line])
    )


def test_moving_down() -> None:
    first, second, third, fourth = create_lines(4)

    assert LineMove(0, 2).apply((first, second, third, fourth)) == (
        second,
        third,
        first,
        fourth,
    )


def test_moving_up() -> None:
    first, second, third, fourth = create_lines(4)

    assert LineMove(3, 0).apply((first, second, third, fourth)) == (
        fourth,
        first,
        second,
        third,
    )


def test_moving_there_and_back() -> None:
    lines = create_lines(4)

    assert LineMove(2, 0).apply(LineMove(0, 2).apply(lines)) == lines


def test_moving_does_not_change_the_given_lines() -> None:
    lines = list(create_lines(3))
    identities = find_identities(lines)

    moved = LineMove(0, 2).apply(lines)

    assert find_identities(lines) == identities
    assert isinstance(moved, tuple)


@pytest.mark.parametrize(
    "move,line_count,message",
    [
        (LineMove(3, 0), 3, "from 3 is not a line position (number of lines: 3)."),
        (LineMove(7, 7), 3, "from 7 is not a line position (number of lines: 3)."),
        (LineMove(-1, 0), 3, "from -1 is not a line position (number of lines: 3)."),
        (LineMove(0, 0), 0, "from 0 is not a line position (number of lines: 0)."),
        (LineMove(0, 3), 3, "to 3 is not a line position (number of lines: 3)."),
        (LineMove(0, -1), 3, "to -1 is not a line position (number of lines: 3)."),
        (LineMove(0, 1), 1, "to 1 is not a line position (number of lines: 1)."),
        (LineMove(1, 1), 3, "the line is already at that position."),
        (LineMove(0, 0), 1, "the line is already at that position."),
    ],
)
def test_invalid_move(move: LineMove, line_count: int, message: str) -> None:
    with pytest.raises(ValueError) as error:
        move.apply(create_lines(line_count))

    assert str(error.value) == f"Invalid line move: {message}"
