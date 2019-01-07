import difflib
from functools import reduce
import pydash


class Differ:
    # pylint: disable=R0903
    def __init__(self, map_, dimensions):
        self._dimensions = dimensions
        self._map = map_

    def diff(self, old, new):
        return difflib.ndiff(
            [self._to_string(entry, self._dimensions) for entry in old],
            [self._to_string(entry, self._dimensions) for entry in new]
        )

    def _to_string(self, line, dimensions):
        if dimensions > 1:
            return ' '.join([
                self._to_string(entry, dimensions - 1)
                for entry in line
            ])
        else:
            return self._map(line)


class Merge:
    def __init__(self, old, new):
        self._old = old
        self._new = new
        self._result = []
        self._old_line = None

    @property
    def current_new(self):
        return self._new[0]

    @property
    def current_old(self):
        return self._old[0]

    @property
    def result(self):
        return self._result

    @property
    def previous_old(self):
        return self._old_line

    def _advance_new(self):
        self._new = self._new[1:]
        self._old_line = None

    def _advance_old(self, save_old_line):
        if save_old_line:
            self._old_line = self.current_old
        self._old = self._old[1:]

    def _append(self, entry):
        self._result.append(entry)

    def delete(self):
        self._advance_old(True)
        return self

    def keep(self):
        self._append(self.current_old)
        self._advance_old(False)
        self._advance_new()
        return self

    def add(self, entry):
        self._append(entry)
        self._advance_new()
        return self


class Merger:
    # pylint: disable=R0903
    def __init__(self, map_, dimensions=1, inner_merge=None):
        self._operations = {
            '- ': lambda state: state.delete(),
            '+ ': self._add_entry,
            '  ': lambda state: state.keep(),
            '? ': pydash.identity
        }
        self._map = map_
        self._dimensions = dimensions
        self._inner_merge = inner_merge

    def _default_inner_merge(self, state):
        return Merger(
            self._map,
            self._dimensions - 1
        ).merge(
            state.previous_old,
            state.current_new
        )

    def _add_entry(self, state):
        new_entry = (
            (self._inner_merge or self._default_inner_merge)(state)
            if (
                self._dimensions > 1 or
                self._inner_merge is not None
            ) and state.previous_old is not None
            else state.current_new
        )
        return state.add(new_entry)

    def merge(self, old, new):
        diff = Differ(self._map, self._dimensions).diff(old, new)
        prefix_length = [len(key) for key in self._operations][0]
        return reduce(
            lambda state, entry: self._operations[entry](state),
            [line[:prefix_length] for line in diff],
            Merge(old, new)
        ).result
