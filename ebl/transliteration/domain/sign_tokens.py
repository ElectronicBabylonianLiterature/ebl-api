from abc import abstractmethod
from typing import Iterable, Tuple, Sequence

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.tokens import Token


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
