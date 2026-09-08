from itertools import zip_longest
from typing import Iterator, Optional, Sequence, Tuple, Type, TypeVar

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import to_sub_index
from ebl.transliteration.domain.converters import (
    convert_flag_sequence,
    convert_string_sequence,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
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


def convert_name_parts(parts: Sequence[ValueToken]) -> Tuple[ValueToken, ...]:
    return tuple(parts)


def convert_name_breaks(breaks: Sequence[BrokenAway]) -> Tuple[BrokenAway, ...]:
    return tuple(breaks)


def _validate_sub_index(
    _instance: object, _attribute: object, value: Optional[int]
) -> None:
    if value is not None and value < 0:
        raise ValueError("Sub-index must be >= 0.")


def _validate_name_parts(
    _instance: object, _attribute: object, value: Sequence[ValueToken]
) -> None:
    wrong = [token for token in value if not isinstance(token, ValueToken)]
    if wrong:
        raise ValueError(
            "name_parts holds value tokens only; "
            f"{type(wrong[0]).__name__} belongs in name_breaks."
        )


def _validate_name_breaks(
    instance: "NamedSign", _attribute: object, value: Sequence[BrokenAway]
) -> None:
    if len(value) > len(instance.name_parts):
        raise ValueError(
            f"A name with {len(instance.name_parts)} parts takes at most "
            f"{len(instance.name_parts)} breaks, not {len(value)}."
        )


NamedSignT = TypeVar("NamedSignT", bound="NamedSign")
LeadingSubIndexSignT = TypeVar(
    "LeadingSubIndexSignT", bound="NamedSignWithLeadingSubIndex"
)


@attr.s(auto_attribs=True, frozen=True)
class NamedSignArguments:
    name: Sequence[ValueToken]
    sub_index: Optional[int] = 1
    modifiers: Sequence[str] = ()
    flags: Sequence[atf.Flag] = ()
    name_breaks: Sequence[BrokenAway] = ()


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name_parts: Sequence[ValueToken] = attr.ib(
        converter=convert_name_parts, validator=_validate_name_parts
    )
    sub_index: Optional[int] = attr.ib(default=1, validator=_validate_sub_index)
    sign: Optional[Token] = None
    name_breaks: Sequence[BrokenAway] = attr.ib(
        default=(), converter=convert_name_breaks, validator=_validate_name_breaks
    )

    @classmethod
    def of_arguments(
        cls: Type[NamedSignT], arguments: NamedSignArguments
    ) -> NamedSignT:
        return cls(
            frozenset(),
            ErasureState.NONE,
            arguments.modifiers,
            arguments.flags,
            arguments.name,
            arguments.sub_index,
            None,
            arguments.name_breaks,
        )

    def with_name(
        self: NamedSignT,
        name_parts: Sequence[ValueToken],
        name_breaks: Sequence[BrokenAway] = (),
    ) -> NamedSignT:
        return attr.evolve(self, name_parts=name_parts, name_breaks=name_breaks)

    def with_sign(self: NamedSignT, sign: Optional[Token]) -> NamedSignT:
        return attr.evolve(self, sign=sign)

    def _interleaved(self) -> Iterator[Token]:
        for part, name_break in zip_longest(self.name_parts, self.name_breaks):
            yield part
            if name_break is not None:
                yield name_break

    @property
    def name_tokens(self) -> Sequence[Token]:
        return tuple(self._interleaved())

    @property
    def name(self) -> str:
        return "".join(part.value for part in self.name_parts)

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
        name = "".join(token.value for token in self._interleaved())
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
        name: Sequence[ValueToken],
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
    ) -> LeadingSubIndexSignT:
        return cls.of_arguments(NamedSignArguments(name, sub_index, modifiers, flags))

    @classmethod
    def of_name(
        cls: Type[LeadingSubIndexSignT],
        name: str,
        sub_index: Optional[int] = 1,
        modifiers: Sequence[str] = (),
        flags: Sequence[atf.Flag] = (),
    ) -> LeadingSubIndexSignT:
        return cls.of((ValueToken.of(name),), sub_index, modifiers, flags)
