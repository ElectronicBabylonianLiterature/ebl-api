from abc import abstractmethod
from typing import Iterable, Tuple, Sequence, Optional

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import int_to_sub_index
from ebl.transliteration.domain.tokens import Token


def convert_string_sequence(strings: Iterable[str]) -> Tuple[str, ...]:
    return tuple(strings)


def convert_flag_sequence(flags: Iterable[atf.Flag]) -> Tuple[atf.Flag, ...]:
    return tuple(flags)


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    flags: Sequence[atf.Flag] = attr.ib(default=tuple(),
                                        converter=convert_flag_sequence)

    @property
    @abstractmethod
    def _sign(self) -> str:
        ...

    @property
    @abstractmethod
    def _type(self) -> str:
        ...

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @property
    def value(self) -> str:
        return f'{self._sign}{"".join(self.string_flags)}'

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': self._type,
            'flags': list(self.string_flags)
        }


@attr.s(auto_attribs=True, frozen=True)
class UnidentifiedSign(AbstractSign):
    @property
    def _sign(self) -> str:
        return atf.UNIDENTIFIED_SIGN

    @property
    def _type(self) -> str:
        return 'UnidentifiedSign'


@attr.s(auto_attribs=True, frozen=True)
class UnclearSign(AbstractSign):
    @property
    def _sign(self) -> str:
        return atf.UNCLEAR_SIGN

    @property
    def _type(self) -> str:
        return 'UnclearSign'


@attr.s(frozen=True, auto_attribs=True)
class Divider(Token):
    divider: str
    modifiers: Tuple[str, ...] = tuple()
    flags: Tuple[atf.Flag, ...] = tuple()

    @property
    def value(self) -> str:
        modifiers = ''.join(self.modifiers)
        flags = ''.join(self.string_flags)
        return f'{self.divider}{modifiers}{flags}'

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Divider',
            'divider': self.divider,
            'modifiers': list(self.modifiers),
            'flags': self.string_flags
        }


@attr.s(auto_attribs=True, frozen=True)
class Reading(Token):
    name: str
    sub_index: Optional[int] = attr.ib(default=None)
    modifiers: Sequence[str] = attr.ib(default=tuple(),
                                       converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(default=tuple(),
                                        converter=convert_flag_sequence)
    sign: Optional[str] = None

    @sub_index.validator
    def _check_sub_index(self, _attribute, value):
        if value is not None and value < 0:
            raise ValueError(
                'Sub-index must be None or >= 0.'
            )

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @property
    def value(self) -> str:
        sub_index = int_to_sub_index(self.sub_index)
        modifiers = ''.join(self.modifiers)
        flags = ''.join(self.string_flags)
        sign = f'({self.sign})' if self.sign else ''
        return f'{self.name}{sub_index}{modifiers}{flags}{sign}'

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Reading',
            'name': self.name,
            'subIndex': self.sub_index,
            'modifiers': list(self.modifiers),
            'flags': list(self.string_flags),
            'sign': self.sign
        }
