from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Iterable, Tuple

import attr
import pydash

from ebl.text.enclosure import Enclosure, EnclosureError, EnclosureValidator, \
    EnclosureVisitor


class ReconstructionToken(ABC):
    @abstractmethod
    def accept(self, visitor: EnclosureVisitor) -> None:
        ...


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

    def accept(self, visitor: EnclosureVisitor) -> None:
        pass


@attr.s(auto_attribs=True, frozen=True)
class StringPart(Part):
    _value: str

    @property
    def is_text(self) -> bool:
        return True

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

    def __str__(self) -> str:
        return str(Lacuna(tuple(), tuple()))


@attr.s(frozen=True)
class SeparatorPart(Part):

    @property
    def is_text(self) -> bool:
        return True

    def __str__(self) -> str:
        return '-'


@attr.s(auto_attribs=True, frozen=True)
class AkkadianWord(ReconstructionToken):

    parts: Tuple[Part, ...]
    modifiers: Tuple[Modifier, ...] = tuple()

    def accept(self, visitor: EnclosureVisitor) -> None:
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
class Lacuna(ReconstructionToken):
    _before: Tuple[Enclosure, ...]
    _after: Tuple[Enclosure, ...]

    def accept(self, visitor: EnclosureVisitor) -> None:
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
class Break(ReconstructionToken):
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


def validate(line: Iterable[ReconstructionToken]):
    validator = EnclosureValidator()
    try:
        for token in line:
            token.accept(validator)
        validator.validate_end_state()
    except EnclosureError as error:
        raise ValueError(f'Invalid line {[str(part) for part in line]}: '
                         f'{error}')
