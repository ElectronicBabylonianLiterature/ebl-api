from abc import abstractmethod
from typing import Sequence, Type, TypeVar

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_flag_sequence
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor

T = TypeVar("T", bound="UnknownSign")


@attr.s(auto_attribs=True, frozen=True)
class UnknownSign(Token):
    flags: Sequence[atf.Flag] = attr.ib(
        default=tuple(), converter=convert_flag_sequence
    )

    @property
    def clean_value(self) -> str:
        return self._sign

    @classmethod
    def of(cls: Type[T], flags: Sequence[atf.Flag] = tuple()) -> T:
        return cls(frozenset(), ErasureState.NONE, flags)

    @property
    def parts(self):
        return tuple()

    @property
    @abstractmethod
    def _sign(self) -> str:
        ...

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @property
    def value(self) -> str:
        return f'{self._sign}{"".join(self.string_flags)}'

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_unknown_sign(self)


@attr.s(auto_attribs=True, frozen=True)
class UnidentifiedSign(UnknownSign):
    @property
    def _sign(self) -> str:
        return atf.UNIDENTIFIED_SIGN


@attr.s(auto_attribs=True, frozen=True)
class UnclearSign(UnknownSign):
    @property
    def _sign(self) -> str:
        return atf.UNCLEAR_SIGN
