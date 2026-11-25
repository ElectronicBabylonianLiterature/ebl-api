from typing import AbstractSet, List, Sequence, Tuple

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_layout import LineLayout, LinePlacement

LINES_FIELD = "lines"
CHAPTER_FIELDS: Sequence[str] = (
    "signs",
    "parser_version",
    "manuscripts",
    "uncertain_fragments",
)
PositionedLine = Tuple[int, Line]


def _validate_run(instance: "LineRun", _attribute: object, value: int) -> None:
    if min(instance.target, instance.source) < 0 or value < 1:
        raise ValueError(f"Invalid line run: {attr.astuple(instance)}.")


@attr.s(frozen=True, auto_attribs=True)
class LineRun:
    target: int
    source: int
    count: int = attr.ib(validator=_validate_run)

    def is_followed_by(self, placement: LinePlacement) -> bool:
        position, source = placement
        return (
            self.target + self.count == position and self.source + self.count == source
        )

    def extend(self) -> "LineRun":
        return attr.evolve(self, count=self.count + 1)


@attr.s(frozen=True, auto_attribs=True)
class KeptContent:
    line_runs: Sequence[LineRun] = ()
    fields: AbstractSet[str] = frozenset()


KEEP_NOTHING = KeptContent()


@attr.s(frozen=True, auto_attribs=True)
class LineEdit:
    position: int
    old: Line
    new: Line


def _append_placement(runs: List[LineRun], placement: LinePlacement) -> List[LineRun]:
    return (
        [*runs[:-1], runs[-1].extend()]
        if runs and runs[-1].is_followed_by(placement)
        else [*runs, LineRun(*placement, 1)]
    )


def _validate_layout(
    instance: "ChapterChange", _attribute: object, value: LineLayout
) -> None:
    old_count = len(instance.old.lines)
    if value.size != len(instance.new.lines) or any(
        source >= old_count for _, source in value.placements
    ):
        raise ValueError(
            f"Line layout {list(value.placements)} of {value.size} lines does not "
            f"fit a change from {old_count} to {len(instance.new.lines)} lines."
        )


@attr.s(frozen=True, auto_attribs=True)
class ChapterChange:
    old: Chapter
    new: Chapter
    layout: LineLayout = attr.ib(validator=_validate_layout)

    @staticmethod
    def in_place(old: Chapter, new: Chapter) -> "ChapterChange":
        return ChapterChange(old, new, LineLayout.in_place(len(old.lines)))

    @property
    def changed_fields(self) -> Sequence[str]:
        return [
            field
            for field in CHAPTER_FIELDS
            if getattr(self.old, field) != getattr(self.new, field)
        ]

    @property
    def edited(self) -> Sequence[LineEdit]:
        return [
            LineEdit(source, self.old.lines[source], self.new.lines[position])
            for position, source in self.layout.stable
            if not self._is_unchanged((position, source))
        ]

    @property
    def removed(self) -> Sequence[PositionedLine]:
        return [
            (position, self.old.lines[position])
            for position in self.layout.find_removed(len(self.old.lines))
        ]

    @property
    def added(self) -> Sequence[PositionedLine]:
        return [(position, self.new.lines[position]) for position in self.layout.added]

    @property
    def unchanged_runs(self) -> Sequence[LineRun]:
        runs: List[LineRun] = []
        for placement in filter(self._is_unchanged, self.layout.placements):
            runs = _append_placement(runs, placement)
        return runs

    @property
    def kept(self) -> KeptContent:
        runs = tuple(self.unchanged_runs)
        fields = {*CHAPTER_FIELDS, *self._find_kept_lines_field(runs)}
        return KeptContent(runs, frozenset(fields.difference(self.changed_fields)))

    def _find_kept_lines_field(self, runs: Sequence[LineRun]) -> Sequence[str]:
        line_count = len(self.new.lines)
        in_place = (LineRun(0, 0, line_count),) if line_count else ()
        is_kept = len(self.old.lines) == line_count and runs == in_place
        return [LINES_FIELD] if is_kept else []

    def _is_unchanged(self, placement: LinePlacement) -> bool:
        position, source = placement
        old_line = self.old.lines[source]
        new_line = self.new.lines[position]
        return old_line is new_line or old_line == new_line
