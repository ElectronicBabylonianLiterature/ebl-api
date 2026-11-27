from typing import Sequence

import attr
import bson
import dictdiffer

from ebl.corpus.application.chapter_changelog import (
    ChapterDiff,
    create_change_diff,
    dump_chapter_document,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_layout import LineLayout, LinePlacement
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.tests.corpus.line_move_support import (
    READINGS,
    create_annotated_line,
    create_signs,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord

KEPT = "kept"
EDITED = "edited"
DELETED = "deleted"
LINE_KINDS: Sequence[str] = (KEPT, EDITED, DELETED)
FIRST_NEW_NUMBER = 200
FIRST_EDITED_NUMBER = 100
STALE_INDEX = 1
STALE_UPDATES: Sequence[Sequence[str]] = (
    (EDITED, KEPT, KEPT, KEPT),
    (DELETED, KEPT, KEPT, KEPT),
    (KEPT, KEPT, KEPT, DELETED),
    (KEPT, KEPT, KEPT, KEPT),
)
OTHER_PARSER_VERSION = "9.9.9"


def create_new_line(number: int) -> Line:
    return create_annotated_line(number, READINGS[number % len(READINGS)])


def edit_line(line: Line, number: int) -> Line:
    return attr.evolve(
        line,
        number=LineNumber(number),
        is_beginning_of_section=not line.is_beginning_of_section,
    )


def _flip_alignment_flag(token: Token) -> Token:
    return (
        token.set_has_variant_alignment(not token.has_variant_alignment)
        if isinstance(token, AbstractWord)
        else token
    )


def _make_variant_stale(variant: LineVariant) -> LineVariant:
    return attr.evolve(
        variant, reconstruction=tuple(map(_flip_alignment_flag, variant.reconstruction))
    )


def make_flags_stale(chapter: Chapter, index: int = STALE_INDEX) -> Chapter:
    stale_line = attr.evolve(
        chapter.lines[index],
        variants=tuple(map(_make_variant_stale, chapter.lines[index].variants)),
    )
    return attr.evolve(
        chapter,
        lines=tuple(
            stale_line if line_index == index else line
            for line_index, line in enumerate(chapter.lines)
        ),
    )


def create_lines_update(
    chapter: Chapter, kinds: Sequence[str], new_count: int, first_number: int = 0
) -> LinesUpdate:
    return LinesUpdate(
        [
            create_new_line(first_number + FIRST_NEW_NUMBER + index)
            for index in range(new_count)
        ],
        {index for index, kind in enumerate(kinds) if kind == DELETED},
        {
            index: edit_line(
                chapter.lines[index], first_number + FIRST_EDITED_NUMBER + index
            )
            for index, kind in enumerate(kinds)
            if kind == EDITED
        },
    )


def create_layout_change(
    chapter: Chapter,
    lines: Sequence[Line],
    placements: Sequence[LinePlacement],
    moved: Sequence[int] = (),
) -> ChapterChange:
    return ChapterChange(
        chapter,
        attr.evolve(
            chapter,
            lines=tuple(lines),
            signs=create_signs(lines),
            parser_version=OTHER_PARSER_VERSION,
        ),
        LineLayout(len(lines), tuple(placements), frozenset(moved)),
    )


def insert_line(chapter: Chapter, position: int) -> ChapterChange:
    placements = [
        (source if source < position else source + 1, source)
        for source in range(len(chapter.lines))
    ]
    lines = list(chapter.lines)
    lines.insert(position, create_new_line(FIRST_NEW_NUMBER))
    return create_layout_change(chapter, lines, placements)


def store_diff(diff: ChapterDiff) -> ChapterDiff:
    return bson.decode(bson.encode({"diff": diff}))["diff"]


def replay(change: ChapterChange) -> dict:
    return dictdiffer.patch(
        store_diff(create_change_diff(change)), dump_chapter_document(change.old)
    )
