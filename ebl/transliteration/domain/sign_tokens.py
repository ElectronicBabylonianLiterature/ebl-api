import re
from abc import abstractmethod
from typing import Iterable, Optional, Sequence, Tuple

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import int_to_sub_index
from ebl.transliteration.domain.tokens import Token, convert_token_sequence


def convert_string_sequence(strings: Iterable[str]) -> Tuple[str, ...]:
    return tuple(strings)


def convert_flag_sequence(flags: Iterable[atf.Flag]) -> Tuple[atf.Flag, ...]:
    return tuple(flags)


@attr.s(auto_attribs=True, frozen=True)
class UnknownSign(Token):
    flags: Sequence[atf.Flag] = attr.ib(
        default=tuple(), converter=convert_flag_sequence
    )

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


@attr.s(auto_attribs=True, frozen=True)
class UnidentifiedSign(UnknownSign):
    @property
    def _sign(self) -> str:
        return atf.UNIDENTIFIED_SIGN

    @property
    def _type(self) -> str:
        return "UnidentifiedSign"


@attr.s(auto_attribs=True, frozen=True)
class UnclearSign(UnknownSign):
    @property
    def _sign(self) -> str:
        return atf.UNCLEAR_SIGN

    @property
    def _type(self) -> str:
        return "UnclearSign"


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    modifiers: Sequence[str] = attr.ib(converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]


@attr.s(frozen=True, auto_attribs=True)
class Divider(AbstractSign):
    divider: str

    @property
    def value(self) -> str:
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        return f"{self.divider}{modifiers}{flags}"

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @staticmethod
    def of(
        divider: str,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
    ):
        return Divider(modifiers, flags, divider)


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name: str = attr.ib()
    sub_index: int = attr.ib()
    sign: Optional[str]

    @abstractmethod
    def _check_name(self, _attribute, value):
        ...

    @sub_index.validator
    def _check_sub_index(self, _attribute, value):
        if value < 0:
            raise ValueError("Sub-index must be >= 0.")

    @property
    def value(self) -> str:
        sub_index = int_to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        sign = f"({self.sign})" if self.sign else ""
        return f"{self.name}{sub_index}{modifiers}{flags}{sign}"


@attr.s(auto_attribs=True, frozen=True)
class Reading(NamedSign):
    def _check_name(self, _attribute, value):
        if not value.islower() and value != "ʾ":
            raise ValueError("Readings must be lowercase.")

    @staticmethod
    def of(
        name: str,
        sub_index: int = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[str] = None,
    ) -> "Reading":
        return Reading(modifiers, flags, name, sub_index, sign)


@attr.s(auto_attribs=True, frozen=True)
class Logogram(NamedSign):
    surrogate: Sequence[Token] = attr.ib(
        default=tuple(), converter=convert_token_sequence
    )

    @property
    def value(self) -> str:
        surrogate = (
            f"<({''.join(token.value for token in self.surrogate)})>"
            if self.surrogate
            else ""
        )
        return f"{super().value}{surrogate}"

    def _check_name(self, _attribute, value):
        if not value.isupper() and value != "ʾ":
            raise ValueError("Logograms must be uppercase.")

    @staticmethod
    def of(
        name: str,
        sub_index: int = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[str] = None,
        surrogate: Sequence[Token] = tuple(),
    ) -> "Logogram":
        return Logogram(modifiers, flags, name, sub_index, sign, surrogate)


@attr.s(auto_attribs=True, frozen=True)
class Number(NamedSign):
    def _check_name(self, _attribute, value):
        if not re.fullmatch(r"[0-9\[\]]+", value):
            raise ValueError("Numbers can only contain decimal digits, [, and ].")

    @staticmethod
    def of(
        name: str,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[str] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number(modifiers, flags, name, sub_index, sign)
