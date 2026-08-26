from typing import Iterable, Optional, Sequence, Tuple, Type, TypeVar, Union

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import to_sub_index
from ebl.transliteration.domain.converters import (
    convert_flag_sequence,
    convert_string_sequence,
)
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    ValueToken,
)


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    modifiers: Sequence[str] = attr.ib(converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]


def name_contribution_of(token: Token) -> str:
    return token.value if isinstance(token, ValueToken) else ""


def _validate_name_contribution(instance, _attribute, value: str) -> None:
    expected = name_contribution_of(instance.token)
    if value != expected:
        raise ValueError(
            f"Name contribution {value!r} does not match "
            f"the contribution {expected!r} of its token."
        )


@attr.s(auto_attribs=True, frozen=True)
class NamePart:
    token: Token
    name_contribution: str = attr.ib(validator=_validate_name_contribution)

    @staticmethod
    def of(token: Token) -> "NamePart":
        return NamePart(token, name_contribution_of(token))

    @property
    def value(self) -> str:
        return self.token.value


NameParts = Sequence[NamePart]
NamePartInput = Union[Token, NamePart]


def convert_name_parts(parts: Iterable[NamePartInput]) -> Tuple[NamePart, ...]:
    return tuple(
        part if isinstance(part, NamePart) else NamePart.of(part) for part in parts
    )


def _validate_sub_index(_instance, _attribute, value: Optional[int]) -> None:
    if value is not None and value < 0:
        raise ValueError("Sub-index must be >= 0.")


NamedSignT = TypeVar("NamedSignT", bound="NamedSign")
LeadingSubIndexSignT = TypeVar(
    "LeadingSubIndexSignT", bound="NamedSignWithLeadingSubIndex"
)


@attr.s(auto_attribs=True, frozen=True)
class NamedSignArguments:
    name: Sequence[Token]
    sub_index: Optional[int] = 1
    modifiers: Sequence[str] = ()
    flags: Sequence[atf.Flag] = ()
    sign: Optional[Token] = None


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name_parts: NameParts = attr.ib(converter=convert_name_parts)
    sub_index: Optional[int] = attr.ib(default=1, validator=_validate_sub_index)
    sign: Optional[Token] = None

    @classmethod
    def _create(cls: Type[NamedSignT], arguments: NamedSignArguments) -> NamedSignT:
        return cls(
            frozenset(),
            ErasureState.NONE,
            arguments.modifiers,
            arguments.flags,
            convert_name_parts(arguments.name),
            arguments.sub_index,
            arguments.sign,
        )

    @property
    def name_tokens(self) -> Sequence[Token]:
        return tuple(part.token for part in self.name_parts)

    @property
    def name(self) -> str:
        return "".join(part.name_contribution for part in self.name_parts)

    @property
    def clean_value(self) -> str:
        sub_index = to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        sign = f"({self.sign.value})" if self.sign else ""
        return f"{self.name}{sub_index}{modifiers}{sign}"

    @property
    def parts(self) -> Sequence[Token]:
        if self.sign:
            return (*self.name_tokens, self.sign)
        else:
            return self.name_tokens

    @property
    def value(self) -> str:
        name = "".join(part.value for part in self.name_parts)
        sub_index = to_sub_index(self.sub_index)
        modifiers = "".join(self.modifiers)
        flags = "".join(self.string_flags)
        sign = f"({self.sign.value})" if self.sign else ""
        return f"{name}{sub_index}{modifiers}{flags}{sign}"

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_named_sign(self)


@attr.s(auto_attribs=True, frozen=True)
class NamedSignWithLeadingSubIndex(NamedSign):
    @classmethod
    def of(
        cls: Type[LeadingSubIndexSignT],
        name: Sequence[Token],
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> LeadingSubIndexSignT:
        return cls._create(NamedSignArguments(name, sub_index, modifiers, flags, sign))

    @classmethod
    def of_name(
        cls: Type[LeadingSubIndexSignT],
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
        sign: Optional[Token] = None,
    ) -> LeadingSubIndexSignT:
        return cls.of((ValueToken.of(name),), sub_index, modifiers, flags, sign)
