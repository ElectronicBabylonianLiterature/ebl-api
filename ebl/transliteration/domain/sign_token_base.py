from typing import Iterable, Optional, Sequence, Tuple, Type, TypeVar

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


@attr.s(auto_attribs=True, frozen=True)
class NamePart:
    token: Token

    @property
    def name_contribution(self) -> str:
        return name_contribution_of(self.token)

    @property
    def value(self) -> str:
        return self.token.value


NameParts = Sequence[NamePart]


def convert_name_parts(parts: Iterable[NamePart]) -> Tuple[NamePart, ...]:
    return tuple(parts)


def name_parts_of(tokens: Iterable[Token]) -> Tuple[NamePart, ...]:
    return tuple(NamePart(token) for token in tokens)


def _validate_sub_index(
    _instance: object, _attribute: object, value: Optional[int]
) -> None:
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
            name_parts_of(arguments.name),
            arguments.sub_index,
        )

    def with_name_tokens(self: NamedSignT, tokens: Sequence[Token]) -> NamedSignT:
        return attr.evolve(self, name_parts=name_parts_of(tokens))

    def with_sign(self: NamedSignT, sign: Optional[Token]) -> NamedSignT:
        return attr.evolve(self, sign=sign)

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
    ) -> LeadingSubIndexSignT:
        return cls._create(NamedSignArguments(name, sub_index, modifiers, flags))

    @classmethod
    def of_name(
        cls: Type[LeadingSubIndexSignT],
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
    ) -> LeadingSubIndexSignT:
        return cls.of((ValueToken.of(name),), sub_index, modifiers, flags)
