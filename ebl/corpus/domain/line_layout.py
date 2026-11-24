from typing import AbstractSet, List, Optional, Sequence, Tuple

import attr

LinePlacement = Tuple[int, int]


def _validate_sources(
    _instance: "LineLayout", _attribute: object, value: Sequence[Optional[int]]
) -> None:
    sources = [source for source in value if source is not None]
    if len(set(sources)) != len(sources) or any(source < 0 for source in sources):
        raise ValueError(f"Invalid line layout: {list(value)}.")


def _validate_moved(
    instance: "LineLayout", _attribute: object, value: AbstractSet[int]
) -> None:
    placed = {position for position, _ in instance.placements}
    sources = [source for _, source in instance.stable]
    if not value <= placed or sources != sorted(sources):
        raise ValueError(
            f"Invalid line layout: {list(instance.sources)} with moved lines "
            f"{sorted(value)}."
        )


@attr.s(frozen=True, auto_attribs=True)
class LineLayout:
    sources: Sequence[Optional[int]] = attr.ib(validator=_validate_sources)
    moved: AbstractSet[int] = attr.ib(default=frozenset(), validator=_validate_moved)

    @staticmethod
    def in_place(line_count: int) -> "LineLayout":
        return LineLayout(tuple(range(line_count)))

    @property
    def placements(self) -> Sequence[LinePlacement]:
        return [
            (position, source)
            for position, source in enumerate(self.sources)
            if source is not None
        ]

    @property
    def stable(self) -> Sequence[LinePlacement]:
        return [
            (position, source)
            for position, source in self.placements
            if position not in self.moved
        ]

    @property
    def added(self) -> Sequence[int]:
        stable = {position for position, _ in self.stable}
        return [
            position for position in range(len(self.sources)) if position not in stable
        ]

    def find_removed(self, line_count: int) -> Sequence[int]:
        stable = {source for _, source in self.stable}
        removed: List[int] = [
            source for source in reversed(range(line_count)) if source not in stable
        ]
        return removed
