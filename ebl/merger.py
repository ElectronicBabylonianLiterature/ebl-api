import difflib
from functools import reduce
import pydash


class Differ:
    # pylint: disable=R0903
    def __init__(self, map_):
        self._map = map_

    def diff(self, old, new):
        return difflib.ndiff(
            [self._map(entry) for entry in old],
            [self._map(entry) for entry in new]
        )


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
    def __init__(self, map_, inner_merge=None):
        self._operations = {
            '- ': lambda state: state.delete(),
            '+ ': self._add_entry,
            '  ': lambda state: state.keep(),
            '? ': pydash.identity
        }
        self._map = map_
        self._inner_merge = inner_merge

    def _add_entry(self, state):
        new_entry = (
            self._inner_merge(state.previous_old, state.current_new)
            if self._inner_merge is not None and state.previous_old is not None
            else state.current_new
        )
        return state.add(new_entry)

    def merge(self, old, new):
        diff = Differ(self._map).diff(old, new)
        prefix_length = [len(key) for key in self._operations][0]
        return reduce(
            lambda state, entry: self._operations[entry](state),
            [line[:prefix_length] for line in diff],
            Merge(old, new)
        ).result
