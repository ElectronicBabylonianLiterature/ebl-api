from itertools import chain, product, starmap
from random import Random
from typing import Callable, List, Optional, Sequence, Tuple

import attr

from ebl.corpus.application.chapter_changes import (
    change_in_place,
    change_lines,
    move_line,
)
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.word_instances_updater import WordInstancesLemmatizer
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.word_instances import WordLemma
from ebl.tests.corpus.chapter_change_support import (
    DELETED,
    KEPT,
    FIRST_EDITED_NUMBER,
    FIRST_NEW_NUMBER,
    LINE_KINDS,
    create_layout_change,
    create_lines_update,
    create_new_line,
    edit_line,
    insert_line,
)
from ebl.tests.corpus.chapter_edit_support import create_manuscripts_update
from ebl.tests.corpus.line_annotation_kind import AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ANNOTATION_KINDS
from ebl.tests.corpus.line_move_support import LINE_COUNT, MOVES
from ebl.tests.corpus.word_instances_support import MOVE_CHAPTER_WORD, NEW_LEMMA
from ebl.transliteration.application.sign_repository import SignRepository

ChangeFactory = Callable[[Chapter, SignRepository], ChapterChange]
NEW_COUNTS: Sequence[int] = (0, 1, 2)
RANDOM_LINE_COUNT = 12
SEEDS: Sequence[int] = tuple(range(12))


@attr.s(frozen=True, auto_attribs=True)
class ChangeCase:
    name: str
    create: ChangeFactory


def _create_lines_case(kinds: Sequence[str], new_count: int) -> ChangeCase:
    return ChangeCase(
        f"lines {''.join(kind[0] for kind in kinds)}+{new_count}",
        lambda chapter, sign_repository: change_lines(
            create_lines_update(chapter, kinds, new_count), sign_repository, chapter
        ),
    )


def _create_move_case(move: LineMove) -> ChangeCase:
    return ChangeCase(
        f"move {move.source} to {move.target}",
        lambda chapter, sign_repository: move_line(move, sign_repository, chapter),
    )


def _create_manuscripts_change(
    chapter: Chapter, sign_repository: SignRepository
) -> ChapterChange:
    update = create_manuscripts_update(chapter, 0)
    return change_in_place(
        ManuscriptUpdater(
            update.manuscripts, update.uncertain_fragments, sign_repository
        ).update,
        chapter,
    )


def _create_annotation_case(kind: AnnotationKind, index: int) -> ChangeCase:
    return ChangeCase(
        f"{kind.name} {index}",
        lambda chapter, _: ChapterChange.in_place(
            chapter, kind.update_line(chapter, index)
        ),
    )


def _create_insert_case(position: int) -> ChangeCase:
    return ChangeCase(
        f"insert at {position}", lambda chapter, _: insert_line(chapter, position)
    )


MANUSCRIPTS_CASE = ChangeCase("manuscripts", _create_manuscripts_change)
LINES_CASES: Sequence[ChangeCase] = tuple(
    _create_lines_case(kinds, new_count)
    for kinds in product(LINE_KINDS, repeat=LINE_COUNT)
    for new_count in NEW_COUNTS
)
INSTANCES_CASE = ChangeCase(
    "instances",
    lambda chapter, _: change_in_place(
        WordInstancesLemmatizer(WordLemma(MOVE_CHAPTER_WORD, NEW_LEMMA)).update,
        chapter,
    ),
)
CHANGE_CASES: Sequence[ChangeCase] = tuple(
    chain(
        LINES_CASES,
        map(_create_move_case, MOVES),
        map(_create_insert_case, range(LINE_COUNT + 1)),
        starmap(_create_annotation_case, product(ANNOTATION_KINDS, range(LINE_COUNT))),
        (MANUSCRIPTS_CASE, INSTANCES_CASE),
    )
)


def delete_line(
    chapter: Chapter, index: int, sign_repository: SignRepository
) -> ChapterChange:
    kinds = [
        DELETED if index == position else KEPT for position in range(len(chapter.lines))
    ]
    return change_lines(
        create_lines_update(chapter, kinds, 0), sign_repository, chapter
    )


def create_random_lines_update(
    chapter: Chapter, random: Random, first_number: int = 0
) -> LinesUpdate:
    return create_lines_update(
        chapter,
        random.choices(LINE_KINDS, weights=(4, 2, 1), k=len(chapter.lines)),
        random.randrange(3),
        first_number,
    )


def _pick_positions(random: Random, count: int, limit: int) -> List[int]:
    return sorted(random.sample(range(count), min(count, random.randrange(limit))))


def create_random_layout_change(chapter: Chapter, random: Random) -> ChapterChange:
    count = len(chapter.lines)
    removed = _pick_positions(random, count, 4)
    edited = _pick_positions(random, count, 4)
    placed: List[Tuple[Optional[int], Line]] = [
        (
            index,
            edit_line(line, FIRST_EDITED_NUMBER + index) if index in edited else line,
        )
        for index, line in enumerate(chapter.lines)
        if index not in removed
    ]
    moved = [placed.pop(random.randrange(len(placed))) for _ in range(2) if placed]
    for number in range(random.randrange(3)):
        placed.insert(
            random.randrange(len(placed) + 1),
            (None, create_new_line(FIRST_NEW_NUMBER + number)),
        )
    for placement in moved:
        placed.insert(random.randrange(len(placed) + 1), placement)
    return create_layout_change(
        chapter,
        [line for _, line in placed],
        [source for source, _ in placed],
        [placed.index(placement) for placement in moved],
    )
