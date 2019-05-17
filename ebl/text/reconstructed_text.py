from abc import ABC, abstractmethod
from enum import unique, Enum
from functools import reduce
from typing import Tuple, Optional, Union, Iterable

import attr


@unique
class Modifier(Enum):
    BROKEN = '#'
    UNCERTAIN = '?'


class BrokenOff(Enum):

    def accept(self, visitor):
        visitor.visit_broken_off(self)


@unique
class BrokenOffOpen(BrokenOff):
    BOTH = '[('
    BROKEN = '['
    MAYBE = '('


@unique
class BrokenOffClose(BrokenOff):
    BOTH = ')]'
    BROKEN = ']'
    MAYBE = ')'


@attr.s(frozen=True)
class Part(ABC):

    @property
    @abstractmethod
    def is_text(self) -> bool:
        ...

    @abstractmethod
    def accept(self, visitor) -> None:
        ...


@attr.s(auto_attribs=True, frozen=True)
class StringPart(Part):
    _value: str

    @property
    def is_text(self) -> bool:
        return True

    def accept(self, visitor) -> None:
        pass

    def __str__(self) -> str:
        return self._value


@attr.s(auto_attribs=True, frozen=True)
class BrokenOffPart(Part):
    _value: BrokenOff

    @property
    def is_text(self) -> bool:
        return False

    def accept(self, visitor) -> None:
        self._value.accept(visitor)

    def __str__(self) -> str:
        return self._value.value


@attr.s(frozen=True)
class LacunaPart(Part):

    @property
    def is_text(self) -> bool:
        return True

    def accept(self, visitor):
        pass

    def __str__(self) -> str:
        return str(Lacuna((None, None)))


@attr.s(frozen=True)
class SeparatorPart(Part):

    @property
    def is_text(self) -> bool:
        return True

    def accept(self, visitor):
        pass

    def __str__(self) -> str:
        return '-'


@attr.s(auto_attribs=True, frozen=True)
class AkkadianWord:

    parts: Tuple[Part, ...]
    modifiers: Tuple[Modifier, ...] = tuple()

    def accept(self, visitor):
        for part in self.parts:
            part.accept(visitor)

    def __str__(self) -> str:
        modifier_string = ''.join([modifier.value
                                   for modifier in self.modifiers])

        def create_string_without_final_broken_off() -> str:
            return ''.join([str(part) for part in self.parts]) +\
                   modifier_string

        def create_string_with_final_broken_off() -> str:
            return ''.join([str(part) for part in self.parts[:-1]]) +\
                   modifier_string + str(self.parts[-1])

        last_part = self.parts[-1]
        return (create_string_without_final_broken_off()
                if last_part.is_text
                else create_string_with_final_broken_off())


@attr.s(auto_attribs=True, frozen=True)
class Lacuna:
    _broken_off: Tuple[Optional[BrokenOffOpen], Optional[BrokenOffClose]]

    def accept(self, visitor):
        for broken_off in self._broken_off:
            if broken_off:
                broken_off.accept(visitor)

    def __str__(self):
        return ''.join(self._generate_parts())

    def _generate_parts(self):
        if self._broken_off[0]:
            yield self._broken_off[0].value
        yield '...'
        if self._broken_off[1]:
            yield self._broken_off[1].value


@attr.s(auto_attribs=True, frozen=True)
class Break(ABC):
    uncertain: bool

    @property
    @abstractmethod
    def _value(self) -> str:
        ...

    def accept(self, visitor):
        pass

    def __str__(self) -> str:
        return f'({self._value})' if self.uncertain else self._value


@attr.s(frozen=True)
class Caesura(Break):

    @property
    def _value(self) -> str:
        return '||'


@attr.s(frozen=True)
class MetricalFootSeparator(Break):

    @property
    def _value(self) -> str:
        return '|'


def validate(line: Iterable[Union[AkkadianWord, Lacuna, Break]]):
    @attr.s(auto_attribs=True)
    class Accumulator:
        state: Tuple[bool, bool] = (False, False)

        def visit_broken_off(self, broken_off):
            expected = {
                BrokenOffOpen.BROKEN: (False, False),
                BrokenOffOpen.MAYBE: (True, False),
                BrokenOffOpen.BOTH: (False, False),
                BrokenOffClose.BROKEN: (True, False),
                BrokenOffClose.MAYBE: (True, True),
                BrokenOffClose.BOTH: (True, True),
            }
            transitions = {
                BrokenOffOpen.BROKEN: (True, False),
                BrokenOffOpen.MAYBE: (True, True),
                BrokenOffOpen.BOTH: (True, True),
                BrokenOffClose.BROKEN: (False, False),
                BrokenOffClose.MAYBE: (True, False),
                BrokenOffClose.BOTH: (False, False),
            }
            if self.state == expected[broken_off]:
                self.state = transitions[broken_off]
            else:
                raise ValueError(f'Unexpected broken off: {broken_off}.')

    def iteratee(accumulator, token):
        token.accept(accumulator)
        return accumulator

    result = reduce(iteratee, line, Accumulator())
    if result.state != (False, False):
        broken_off = []
        if result.state[1]:
            broken_off.append(BrokenOffClose.MAYBE)
        if result.state[0]:
            broken_off.append(BrokenOffClose.BROKEN)
        raise ValueError(f'Unclosed broken off {broken_off}.')
