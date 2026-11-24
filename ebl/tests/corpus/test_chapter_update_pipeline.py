from typing import Any, Dict, List, Sequence

import pytest

from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import (
    CHAPTER_FIELDS,
    KEEP_NOTHING,
    LINES_FIELD,
    KeptContent,
    LineRun,
)
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line import Line
from ebl.corpus.infrastructure.chapter_update_pipeline import (
    create_chapter_update,
    create_lines_expression,
    create_lines_update,
    create_literal,
)
from ebl.tests.corpus.line_move_support import LINE_COUNT, create_move_chapter
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump

REVISION = "0123456789abcdef01234567"
FIELD_KEYS: Sequence[str] = (
    "signs",
    "parserVersion",
    "manuscripts",
    "uncertainFragments",
)


@pytest.fixture
def chapter() -> Chapter:
    return create_move_chapter()


def dump_lines(lines: Sequence[Line]) -> Dict[str, Any]:
    return {"$literal": [stored_dump(LineSchema(), line) for line in lines]}


def slice_lines(source: int, count: int) -> Dict[str, Any]:
    return {"$slice": ["$lines", source, count]}


def test_literal() -> None:
    assert create_literal("$lines") == {"$literal": "$lines"}


def test_lines_without_runs_are_dumped(chapter: Chapter) -> None:
    assert create_lines_expression(chapter.lines, ()) == {
        "$concatArrays": [dump_lines(chapter.lines)]
    }


def test_no_lines_are_an_empty_literal() -> None:
    assert create_lines_expression((), ()) == {"$literal": []}


def test_dumped_lines_are_stored_sparse(chapter: Chapter) -> None:
    assert has_key(LineSchema().dump(chapter.lines[0]), "erasure")
    assert not has_key(create_lines_expression(chapter.lines, ()), "erasure")
    assert not has_key(
        create_chapter_update(chapter, KEEP_NOTHING, REVISION), "erasure"
    )
    assert not has_key(create_lines_update({0: chapter.lines[0]}, REVISION), "erasure")


@pytest.mark.parametrize(
    "runs,segments",
    [
        ([LineRun(0, 0, 4)], [("slice", 0, 4)]),
        ([LineRun(0, 1, 4)], [("slice", 1, 4)]),
        ([LineRun(0, 0, 1)], [("slice", 0, 1), ("dump", 1, 4)]),
        ([LineRun(3, 7, 1)], [("dump", 0, 3), ("slice", 7, 1)]),
        ([LineRun(1, 0, 2)], [("dump", 0, 1), ("slice", 0, 2), ("dump", 3, 4)]),
        (
            [LineRun(0, 2, 1), LineRun(1, 0, 1), LineRun(3, 3, 1)],
            [("slice", 2, 1), ("slice", 0, 1), ("dump", 2, 3), ("slice", 3, 1)],
        ),
        (
            [LineRun(1, 5, 1), LineRun(3, 6, 1)],
            [("dump", 0, 1), ("slice", 5, 1), ("dump", 2, 3), ("slice", 6, 1)],
        ),
    ],
)
def test_lines_are_stored_runs_and_dumped_lines_in_order(
    chapter: Chapter, runs: Sequence[LineRun], segments: Sequence[tuple]
) -> None:
    assert create_lines_expression(chapter.lines, runs) == {
        "$concatArrays": [
            slice_lines(first, second)
            if kind == "slice"
            else dump_lines(chapter.lines[first:second])
            for kind, first, second in segments
        ]
    }


@pytest.mark.parametrize(
    "runs",
    [
        [LineRun(0, 0, 5)],
        [LineRun(4, 0, 1)],
        [LineRun(0, 0, 2), LineRun(1, 2, 1)],
        [LineRun(2, 0, 1), LineRun(0, 1, 1)],
    ],
)
def test_runs_that_do_not_fit_the_lines(
    chapter: Chapter, runs: Sequence[LineRun]
) -> None:
    with pytest.raises(ValueError, match=f"not a part of {LINE_COUNT} lines"):
        create_lines_expression(chapter.lines, runs)


def test_update_that_keeps_nothing_sets_every_field(chapter: Chapter) -> None:
    dumped = stored_dump(ChapterSchema(), chapter)

    assert create_chapter_update(chapter, KEEP_NOTHING, REVISION) == [
        {
            "$set": {
                "lines": {"$concatArrays": [{"$literal": dumped["lines"]}]},
                **{key: {"$literal": dumped[key]} for key in FIELD_KEYS},
                "_cacheRevision": {"$literal": REVISION},
            }
        }
    ]


def test_update_that_keeps_everything_sets_the_revision(chapter: Chapter) -> None:
    kept = KeptContent((LineRun(0, 0, LINE_COUNT),), {LINES_FIELD, *CHAPTER_FIELDS})

    assert create_chapter_update(chapter, kept, REVISION) == [
        {"$set": {"_cacheRevision": {"$literal": REVISION}}}
    ]


@pytest.mark.parametrize(
    "field,key",
    [
        ("signs", "signs"),
        ("parser_version", "parserVersion"),
        ("manuscripts", "manuscripts"),
        ("uncertain_fragments", "uncertainFragments"),
    ],
)
def test_update_sets_a_field_that_is_not_kept(
    chapter: Chapter, field: str, key: str
) -> None:
    kept = KeptContent((), {LINES_FIELD, *CHAPTER_FIELDS} - {field})

    assert create_chapter_update(chapter, kept, REVISION) == [
        {
            "$set": {
                key: {"$literal": stored_dump(ChapterSchema(), chapter)[key]},
                "_cacheRevision": {"$literal": REVISION},
            }
        }
    ]


def test_update_sets_the_lines_from_the_runs(chapter: Chapter) -> None:
    runs = (LineRun(0, 1, 2), LineRun(3, 0, 1))
    (stage,) = create_chapter_update(
        chapter, KeptContent(runs, frozenset(CHAPTER_FIELDS)), REVISION
    )

    assert stage == {
        "$set": {
            "lines": create_lines_expression(chapter.lines, runs),
            "_cacheRevision": {"$literal": REVISION},
        }
    }


def find_operators(update: List[dict]) -> List[List[str]]:
    (stage,) = update
    return [list(value) for value in stage["$set"].values()]


def test_every_value_of_an_update_is_an_expression(chapter: Chapter) -> None:
    update = create_chapter_update(
        chapter, KeptContent((LineRun(1, 1, 1),)), LEGACY_REVISION
    )
    segments = update[0]["$set"]["lines"]["$concatArrays"]

    assert find_operators(update) == [["$concatArrays"], *[["$literal"]] * 5]
    assert [list(segment) for segment in segments] == [
        ["$literal"],
        ["$slice"],
        ["$literal"],
    ]


def test_lines_update_sets_the_lines_at_their_positions(chapter: Chapter) -> None:
    lines = {0: chapter.lines[1], 3: chapter.lines[2]}

    assert create_lines_update(lines, REVISION) == {
        "$set": {
            "lines.0": stored_dump(LineSchema(), chapter.lines[1]),
            "lines.3": stored_dump(LineSchema(), chapter.lines[2]),
            "_cacheRevision": REVISION,
        }
    }


def test_lines_update_without_lines_sets_the_revision() -> None:
    assert create_lines_update({}, REVISION) == {"$set": {"_cacheRevision": REVISION}}


def test_lines_update_at_a_negative_position(chapter: Chapter) -> None:
    with pytest.raises(ValueError, match="Invalid line position: -1"):
        create_lines_update({-1: chapter.lines[0]}, REVISION)
