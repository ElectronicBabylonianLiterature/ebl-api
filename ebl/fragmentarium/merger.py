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
    def old_line(self):
        return self._old_line

    def advance_new(self):
        self._new = self._new[1:]
        self._old_line = None

    def advance_old(self, save_old_line=False):
        if save_old_line:
            self._old_line = self.current_old
        self._old = self._old[1:]

    def append(self, entry):
        self._result.append(entry)


class Merger:
    # pylint: disable=R0903
    def __init__(self, map_, dimensions):
        self._operations = {
            '- ': self._delete_entry,
            '+ ': self._add_entry,
            '  ': self._keep_entry,
            '? ': pydash.identity
        }
        self._map = map_
        self._dimensions = dimensions

    @staticmethod
    def _delete_entry(state):
        state.advance_old(True)
        return state

    def _inner_merge(self, state):
        return Merger(self._map, self._dimensions - 1).merge(
            state.old_line,
            state.current_new
        )

    def _add_entry(self, state):
        new_entry = (self._inner_merge(state)
                     if self._dimensions > 1 and state.old_line is not None
                     else state.current_new)
        state.append(new_entry)
        state.advance_new()
        return state

    @staticmethod
    def _keep_entry(state):
        state.append(state.current_old)
        state.advance_new()
        state.advance_old()
        return state

    def merge(self, old, new):
        diff = Differ(self._map, self._dimensions).diff(old, new)
        return reduce(
            lambda state, entry: self._operations[entry](state),
            [line[:2] for line in diff],
            Merge(old, new)
        ).result
