import difflib
from functools import reduce
import pydash


def diff(old, new, create_entry):
    return difflib.ndiff(
        [create_entry(token) for token in old],
        [create_entry(token) for token in new]
    )


def diff_row(old, new):
    return diff(old, new, lambda token: token['value'])


def diff_lemmatization(old, new):
    return diff(
        old,
        new,
        lambda line: ' '.join([token['value'] for token in line])
    )


class State:
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
    def __init__(self, recursive):
        self._operations = {
            '- ': self._delete_entry,
            '+ ': self._add_entry,
            '  ': self._keep_entry,
            '? ': pydash.noop
        }
        self._recursive = recursive

    @staticmethod
    def _delete_entry(state):
        state.advance_old(True)

    @staticmethod
    def _inner_merge(state):
        return Merger(False).merge(
            state.old_line,
            state.current_new,
            diff_row
        )

    def _add_entry(self, state):
        new_entry = (self._inner_merge(state)
                     if self._recursive and state.old_line is not None
                     else state.current_new)
        state.append(new_entry)
        state.advance_new()

    @staticmethod
    def _keep_entry(state):
        state.append(state.current_old)
        state.advance_new()
        state.advance_old()

    def merge(self, old, new, differ):
        def merge_entry(state, entry):
            self._operations[entry](state)
            return state

        return reduce(
            merge_entry,
            [line[:2] for line in differ(old, new)],
            State(old, new)
        ).result
