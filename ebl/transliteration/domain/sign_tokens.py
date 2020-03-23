from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeVar, Union

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import to_sub_index
from ebl.transliteration.domain.converters import (
    convert_flag_sequence,
    convert_string_sequence,
    convert_token_sequence,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.tokens import Token, ValueToken

T = TypeVar("T", bound="UnknownSign")


@attr.s(auto_attribs=True, frozen=True)
class UnknownSign(Token):
    flags: Sequence[atf.Flag] = attr.ib(
        default=tuple(), converter=convert_flag_sequence
    )

    @classmethod
    def of(cls: Type[T], flags: Sequence[atf.Flag] = tuple()) -> T:
        return cls(frozenset(), flags)

    @property
    def parts(self):
        return tuple()

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
    def parts(self):
        return tuple()

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @staticmethod
    def of(
        divider: str,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
    ):
        return Divider(frozenset(), modifiers, flags, divider)


SignName = Sequence[Union[ValueToken, BrokenAway]]


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name_parts: SignName = attr.ib(converter=convert_token_sequence)
    sub_index: Optional[int] = attr.ib(default=1)
    sign: Optional[Token] = None

    @sub_index.validator
    def _check_sub_index(self, _attribute, value):
        if value is not None and value < 0:
            raise ValueError("Sub-index must be >= 0.")

    @property
    def name(self) -> str:
        return "".join(
            token.value for token in self.name_parts if type(token) == ValueToken
        )

    @property
    def parts(self) -> Sequence[Token]:
        if self.sign:
            return (*self.name_parts, self.sign)
        else:
            return self.name_parts

    @property
    def value(self) -> str:
        name = "".join(token.value for token in self.name_parts)
        sub_index = to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        sign = f"({self.sign.value})" if self.sign else ""
        return f"{name}{sub_index}{modifiers}{flags}{sign}"


@attr.s(auto_attribs=True, frozen=True)
class Reading(NamedSign):
    @staticmethod
    def of(
        name: SignName,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
    ) -> "Reading":
        return Reading(frozenset(), modifiers, flags, name, sub_index, sign)

    @staticmethod
    def of_name(
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
    ) -> "Reading":
        return Reading.of((ValueToken.of(name),), sub_index, modifiers, flags, sign)


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

    @staticmethod
    def of(
        name: SignName,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
        surrogate: Sequence[Token] = tuple(),
    ) -> "Logogram":
        return Logogram(frozenset(), modifiers, flags, name, sub_index, sign, surrogate)

    @staticmethod
    def of_name(
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
        surrogate: Sequence[Token] = tuple(),
    ) -> "Logogram":
        return Logogram.of(
            (ValueToken.of(name),), sub_index, modifiers, flags, sign, surrogate
        )


@attr.s(auto_attribs=True, frozen=True)
class Number(NamedSign):
    @staticmethod
    def of(
        name: SignName,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number(frozenset(), modifiers, flags, name, sub_index, sign)

    @staticmethod
    def of_name(
        name: str,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
        sign: Optional[Token] = None,
        sub_index: int = 1,
    ) -> "Number":
        return Number.of((ValueToken.of(name),), modifiers, flags, sign, sub_index)


@attr.s(auto_attribs=True, frozen=True)
class Grapheme(AbstractSign):
    name: str

    @property
    def value(self) -> str:
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        return f"{self.name}{modifiers}{flags}"

    @property
    def parts(self):
        return tuple()

    @staticmethod
    def of(
        name: str,
        modifiers: Sequence[str] = tuple(),
        flags: Sequence[atf.Flag] = tuple(),
    ) -> "Grapheme":
        return Grapheme(frozenset(), modifiers, flags, name)


@attr.s(auto_attribs=True, frozen=True)
class CompoundGrapheme(ValueToken):
    pass
