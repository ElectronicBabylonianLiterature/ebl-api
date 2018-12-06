import difflib
import pydash


class State:
    def __init__(self, old, new):
        self._old = old
        self._new = new
        self._result = []
        self._old_index = 0
        self._new_index = 0
        self._old_line = None

    @property
    def current_new(self):
        return self._new[self._new_index]

    @property
    def current_old(self):
        return self._old[self._old_index]

    @property
    def result(self):
        return self._result

    @property
    def old_line(self):
        return self._old_line

    def advance_new(self):
        self._new_index += 1
        self._old_line = None

    def advance_old(self, save_old_line=False):
        if save_old_line:
            self._old_line = self.current_old
        self._old_index += 1

    def append(self, entry):
        self._result.append(entry)


class Merger:
    def __init__(self, recursive):
        self._operations = {
            '- ': self._delete_entry,
            '+ ': self._add_entry,
            '  ': self._keep_entry,
            '? ': pydash.noop
        }
        self._recursive = recursive

    def _delete_entry(self, state):
        state.advance_old(True)

    def _add_entry(self, state):
        if self._recursive and state.old_line is not None:
            inner_diff = difflib.ndiff(
                [
                    token['value']
                    for token in state.old_line  # pylint: disable=E1133
                ],
                [
                    token['value']
                    for token in state.current_new
                ]
            )
            merged = Merger(False).merge(
                state.old_line,
                state.current_new,
                inner_diff
            )
            state.append(merged)
        else:
            state.append(state.current_new)
        state.advance_new()

    def _keep_entry(self, state):
        state.append(state.current_old)
        state.advance_new()
        state.advance_old()

    def merge(self, old, new, diff):
        state = State(old, new)

        for line in diff:
            prefix = line[:2]
            self._operations[prefix](state)

        return state.result
