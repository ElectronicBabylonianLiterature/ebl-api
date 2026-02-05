import difflib
from collections import deque
from functools import reduce
from typing import (
    Callable,
    Deque,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
)

T = TypeVar("T")
DiffMapping = Callable[[T], str]
InnerMerge = Callable[[T, T], T]


class Merge(Generic[T]):
    def __init__(self, old: Sequence[T], new: Sequence[T]) -> None:
        self._old: Deque[T] = deque(old)
        self._new: Deque[T] = deque(new)
        self._result: Deque[T] = deque()
        self._edited: Deque[T] = deque()

    @property
    def current_new(self) -> T:
        return self._new[0]

    @property
    def result(self) -> List[T]:
        return list(self._result)

    def pop_edited(self) -> Optional[T]:
        try:
            return self._edited.popleft()
        except IndexError:
            return None

    def _advance_new(self) -> None:
        self._new.popleft()

    def _advance_old(self, is_edited: bool) -> T:
        old = self._old.popleft()
        if is_edited:
            self._edited.append(old)
        return old

    def _append(self, entry: T) -> None:
        self._result.append(entry)

    def delete(self) -> "Merge":
        self._advance_old(True)
        return self

    def keep(self) -> "Merge":
        self._append(self._advance_old(False))
        self._advance_new()
        return self

    def add(self, entry: T) -> "Merge":
        self._append(entry)
        self._advance_new()
        return self


def take_new(_: T, new: T) -> T:
    return new


class Merger(Generic[T]):
    def __init__(
        self, map_: DiffMapping[T], inner_merge: Optional[InnerMerge[T]] = None
    ) -> None:
        self._operations: Mapping[str, Callable[[Merge[T]], Merge[T]]] = {
            "- ": lambda state: state.delete(),
            "+ ": self._add_entry,
            "  ": lambda state: state.keep(),
            "? ": lambda state: state,
        }
        self._map: DiffMapping[T] = map_
        self._merge_strategy: InnerMerge[T] = inner_merge or take_new

    def _add_entry(self, state: Merge[T]) -> Merge[T]:
        new_entry = self._inner_merge(state.pop_edited(), state.current_new)
        return state.add(new_entry)

    def _inner_merge(self, old: Optional[T], new: T) -> T:
        return self._merge_strategy(old, new) if old is not None else new

    def _diff(self, old: Sequence[T], new: Sequence[T]) -> Iterator[str]:
        return difflib.ndiff(
            [self._map(entry) for entry in old], [self._map(entry) for entry in new]
        )

    def merge(self, old: Sequence[T], new: Sequence[T]) -> List[T]:
        diff = self._diff(old, new)
        prefix_length = [len(key) for key in self._operations][0]
        return reduce(
            lambda state, entry: self._operations[entry](state),
            [line[:prefix_length] for line in diff],
            Merge(old, new),
        ).result
