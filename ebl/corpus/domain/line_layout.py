from typing import AbstractSet, List, Sequence, Tuple

import attr

LinePlacement = Tuple[int, int]


def _validate_placements(
    instance: "LineLayout", _attribute: object, value: Sequence[LinePlacement]
) -> None:
    positions = [position for position, _ in value]
    sources = [source for _, source in value]
    if (
        positions != sorted(set(positions))
        or len(set(sources)) != len(sources)
        or any(not 0 <= position < instance.size for position in positions)
        or any(source < 0 for source in sources)
    ):
        raise ValueError(
            f"Invalid line layout: {list(value)} in {instance.size} lines."
        )


def _validate_moved(
    instance: "LineLayout", _attribute: object, value: AbstractSet[int]
) -> None:
    placed = {position for position, _ in instance.placements}
    sources = [source for _, source in instance.stable]
    if not value <= placed or sources != sorted(sources):
        raise ValueError(
            f"Invalid line layout: {list(instance.placements)} with moved lines "
            f"{sorted(value)}."
        )


@attr.s(frozen=True, auto_attribs=True)
class LineLayout:
    size: int
    placements: Sequence[LinePlacement] = attr.ib(validator=_validate_placements)
    moved: AbstractSet[int] = attr.ib(default=frozenset(), validator=_validate_moved)

    @staticmethod
    def in_place(line_count: int) -> "LineLayout":
        return LineLayout.of_sources(range(line_count))

    @staticmethod
    def of_sources(
        sources: Sequence[int], added: int = 0, moved: AbstractSet[int] = frozenset()
    ) -> "LineLayout":
        return LineLayout(len(sources) + added, tuple(enumerate(sources)), moved)

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
        return [position for position in range(self.size) if position not in stable]

    def find_removed(self, line_count: int) -> Sequence[int]:
        stable = {source for _, source in self.stable}
        removed: List[int] = [
            source for source in reversed(range(line_count)) if source not in stable
        ]
        return removed
