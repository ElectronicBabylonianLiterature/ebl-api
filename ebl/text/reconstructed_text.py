from abc import ABC, abstractmethod
from enum import Enum, unique
from functools import reduce
from typing import Iterable, Tuple, Union

import attr
import pydash

from ebl.text.enclosure import EnclosureType, EnclosureVariant, Enclosure, \
    EnclosureVisitor


@unique
class Modifier(Enum):
    BROKEN = '#'
    UNCERTAIN = '?'
    CORRECTED = '!'


@attr.s(frozen=True)
class Part(ABC):

    @property
    @abstractmethod
    def is_text(self) -> bool:
        ...

    @abstractmethod
    def accept(self, visitor: EnclosureVisitor) -> None:
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
class EnclosurePart(Part):
    _value: Enclosure

    @property
    def is_text(self) -> bool:
        return False

    def accept(self, visitor: EnclosureVisitor) -> None:
        self._value.accept(visitor)

    def __str__(self) -> str:
        return str(self._value)


@attr.s(frozen=True)
class LacunaPart(Part):

    @property
    def is_text(self) -> bool:
        return True

    def accept(self, visitor):
        pass

    def __str__(self) -> str:
        return str(Lacuna(tuple(), tuple()))


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

    def accept(self, visitor: EnclosureVisitor):
        for part in self.parts:
            part.accept(visitor)

    def __str__(self) -> str:
        last_parts = pydash.take_right_while(list(self.parts),
                                             lambda part: not part.is_text)
        return ''.join(
            [str(part)
             for part
             in self.parts[:len(self.parts) - len(last_parts)]] +
            [modifier.value for modifier in self.modifiers] +
            [str(part) for part in last_parts]
        )


@attr.s(auto_attribs=True, frozen=True)
class Lacuna:
    _before: Tuple[Enclosure, ...]
    _after: Tuple[Enclosure, ...]

    def accept(self, visitor: EnclosureVisitor):
        for enclosure in self._before + self._after:
            enclosure.accept(visitor)

    def __str__(self):
        return ''.join(self._generate_parts())

    def _generate_parts(self):
        for enclosure in self._before:
            yield str(enclosure)
        yield '...'
        for enclosure in self._after:
            yield str(enclosure)


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
    class EnclosureValidator(EnclosureVisitor):
        def __init__(self):
            self.state = {
                EnclosureType.BROKEN_OFF: False,
                EnclosureType.MAYBE_BROKEN_OFF: False
            }

        def visit_enclosure(self, enclosure: Enclosure) -> None:
            expected = {
                EnclosureType.BROKEN_OFF: None,
                EnclosureType.MAYBE_BROKEN_OFF: EnclosureType.BROKEN_OFF
            }
            expected_type = expected[enclosure.type]
            if (enclosure.variant is EnclosureVariant.OPEN and
                    not self.state[enclosure.type] and
                    (not expected_type or self.state[expected_type])):
                self.state[enclosure.type] = True
            elif (enclosure.variant is EnclosureVariant.CLOSE and
                  self.state[enclosure.type] and
                  not [type_
                       for type_, open_
                       in self.state.items()
                       if open_ and expected[type_] is enclosure.type]):
                self.state[enclosure.type] = False
            else:
                raise ValueError(f'Unexpected enclosure {enclosure} '
                                 f'in {[str(part) for part in line]}.')

    def iteratee(accumulator, token):
        token.accept(accumulator)
        return accumulator

    result = reduce(iteratee, line, EnclosureValidator())
    open_enclosures = [type_
                       for type_, open_ in result.state.items()
                       if open_]
    if open_enclosures:
        raise ValueError(f'Unclosed enclosure {open_enclosures} '
                         f'in line {[str(part) for part in line]}.')
