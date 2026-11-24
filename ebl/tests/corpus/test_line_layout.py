from typing import Optional, Sequence, Set

import pytest

from ebl.corpus.domain.line_layout import LineLayout
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    MOVES,
    READINGS,
    create_annotated_line,
    reorder,
)

Sources = Sequence[Optional[int]]
LINE = create_annotated_line(1, READINGS[0])


def test_layout_of_lines_in_place() -> None:
    layout = LineLayout.in_place(3)

    assert layout == LineLayout((0, 1, 2), frozenset())
    assert layout.placements == [(0, 0), (1, 1), (2, 2)]
    assert layout.stable == layout.placements
    assert layout.added == []
    assert layout.find_removed(3) == []


def test_layout_of_no_lines() -> None:
    layout = LineLayout.in_place(0)

    assert layout.sources == ()
    assert layout.placements == []
    assert layout.find_removed(0) == []


def test_layout_with_removed_new_and_moved_lines() -> None:
    layout = LineLayout((None, 3, 0, 4, None), frozenset({2}))

    assert layout.placements == [(1, 3), (2, 0), (3, 4)]
    assert layout.stable == [(1, 3), (3, 4)]
    assert layout.added == [0, 2, 4]
    assert layout.find_removed(6) == [5, 2, 1, 0]


@pytest.mark.parametrize(
    "sources,moved",
    [
        ((0, 0), set()),
        ((1, None, 1), set()),
        ((-1,), set()),
        ((1, 0), set()),
        ((0, 2, 1), set()),
        ((0, 1), {2}),
        ((None, 0), {0}),
        ((2, 1, 0), {0}),
    ],
)
def test_invalid_layout(sources: Sources, moved: Set[int]) -> None:
    with pytest.raises(ValueError, match="Invalid line layout"):
        LineLayout(sources, frozenset(moved))


@pytest.mark.parametrize(
    "deleted,edited,new_count,sources",
    [
        (set(), set(), 0, (0, 1, 2, 3)),
        ({0}, set(), 0, (1, 2, 3)),
        ({3}, set(), 1, (0, 1, 2, None)),
        ({1, 2}, {0}, 2, (0, 3, None, None)),
        ({0, 1, 2, 3}, set(), 0, ()),
        ({0, 1, 2, 3}, set(), 1, (None,)),
        ({1}, {1}, 0, (0, 1, 2, 3)),
        ({4, -1}, {7}, 0, (0, 1, 2, 3)),
    ],
)
def test_layout_of_a_lines_update(
    deleted: Set[int], edited: Set[int], new_count: int, sources: Sources
) -> None:
    update = LinesUpdate([LINE] * new_count, deleted, dict.fromkeys(edited, LINE))

    assert update.create_layout(LINE_COUNT) == LineLayout(sources)
    assert update.find_kept(LINE_COUNT) == [
        source for source in sources if source is not None
    ]


@pytest.mark.parametrize("move", MOVES)
def test_layout_of_a_move(move: LineMove) -> None:
    layout = move.create_layout(LINE_COUNT)

    assert layout == LineLayout(
        reorder(range(LINE_COUNT), move), frozenset({move.target})
    )
    assert layout.added == [move.target]
    assert layout.find_removed(LINE_COUNT) == [move.source]


def test_layout_of_an_invalid_move() -> None:
    with pytest.raises(ValueError, match="Invalid line move"):
        LineMove(0, LINE_COUNT).create_layout(LINE_COUNT)
