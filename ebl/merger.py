import difflib
from functools import reduce
from queue import SimpleQueue, Empty
from typing import (Callable, Generic, Iterator, List, Mapping, Optional,
                    Sequence, TypeVar)

import pydash

T = TypeVar('T')
DiffMapping = Callable[[T], str]
InnerMerge = Optional[Callable[[T, T], T]]


class Merge(Generic[T]):
    def __init__(self, old: Sequence[T], new: Sequence[T]) -> None:
        self._old: Sequence[T] = old
        self._new: Sequence[T] = new
        self._result: List[T] = []
        self._old_line: SimpleQueue[T] = SimpleQueue()

    @property
    def current_new(self) -> T:
        return self._new[0]

    @property
    def current_old(self) -> T:
        return self._old[0]

    @property
    def result(self) -> List[T]:
        return self._result

    def get_previous_old(self) -> Optional[T]:
        try:
            return self._old_line.get_nowait()
        except Empty:
            return None

    def _advance_new(self) -> None:
        self._new = self._new[1:]
        # self._old_line = None

    def _advance_old(self, save_old_line: bool) -> None:
        if save_old_line:
            self._old_line.put(self.current_old)
        self._old = self._old[1:]

    def _append(self, entry: T) -> None:
        self._result.append(entry)

    def delete(self) -> 'Merge':
        self._advance_old(True)
        return self

    def keep(self) -> 'Merge':
        self._append(self.current_old)
        self._advance_old(False)
        self._advance_new()
        return self

    def add(self, entry: T) -> 'Merge':
        self._append(entry)
        self._advance_new()
        return self


class Merger(Generic[T]):

    def __init__(
            self,
            map_: DiffMapping[T],
            inner_merge: InnerMerge[T] = None
    ) -> None:
        self._operations: Mapping[str, Callable[[Merge[T]], Merge[T]]] = {
            '- ': lambda state: state.delete(),
            '+ ': self._add_entry,
            '  ': lambda state: state.keep(),
            '? ': pydash.identity
        }
        self._map: DiffMapping[T] = map_
        self._inner_merge: InnerMerge[T] = inner_merge

    def _add_entry(self, state: Merge[T]) -> Merge[T]:
        previous_old = state.get_previous_old()
        new_entry = (
            self._inner_merge(previous_old, state.current_new)
            if self._inner_merge is not None and previous_old is not None
            else state.current_new
        )
        return state.add(new_entry)

    def _diff(self, old: Sequence[T], new: Sequence[T]) -> Iterator[str]:
        return difflib.ndiff(
            [self._map(entry) for entry in old],
            [self._map(entry) for entry in new]
        )

    def merge(self, old: Sequence[T], new: Sequence[T]) -> List[T]:
        diff = self._diff(old, new)
        prefix_length = [len(key) for key in self._operations][0]
        return reduce(
            lambda state, entry: self._operations[entry](state),
            [line[:prefix_length] for line in diff],
            Merge(old, new)
        ).result
