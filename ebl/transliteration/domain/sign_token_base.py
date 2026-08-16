from typing import AbstractSet, Iterable, Optional, Sequence, Tuple, TypeVar

import attr

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.atf import to_sub_index
from ebl.transliteration.domain.converters import (
    convert_flag_sequence,
    convert_string_sequence,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    ValueToken,
)

TokenT = TypeVar("TokenT", bound=Token)


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    modifiers: Sequence[str] = attr.ib(converter=convert_string_sequence)
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]


@attr.s(auto_attribs=True, frozen=True)
class NamePart(Token):
    token: Token
    name_contribution: str

    @staticmethod
    def of(token: Token) -> "NamePart":
        return NamePart(
            token.enclosure_type,
            token.erasure,
            token,
            token.value if isinstance(token, ValueToken) else "",
        )

    @property
    def value(self) -> str:
        return self.token.value

    @property
    def clean_value(self) -> str:
        return self.token.clean_value

    @property
    def parts(self) -> Sequence[Token]:
        return self.token.parts

    @property
    def lemmatizable(self) -> bool:
        return self.token.lemmatizable

    @property
    def alignable(self) -> bool:
        return self.token.alignable

    def get_key(self) -> str:
        return self.token.get_key()

    def set_unique_lemma(self, lemma: LemmatizationToken) -> "NamePart":
        return NamePart.of(self.token.set_unique_lemma(lemma))

    def update_alignment(self, alignment_map) -> "NamePart":
        return NamePart.of(self.token.update_alignment(alignment_map))

    def set_enclosure_type(
        self, enclosure_type: AbstractSet[EnclosureType]
    ) -> "NamePart":
        return NamePart.of(self.token.set_enclosure_type(enclosure_type))

    def set_erasure(self, erasure: ErasureState) -> "NamePart":
        return NamePart.of(self.token.set_erasure(erasure))

    def merge(self, token: TokenT) -> TokenT:
        return self.token.merge(token)

    def accept(self, visitor: TokenVisitor) -> None:
        self.token.accept(visitor)


NameParts = Sequence[NamePart]


def convert_name_parts(parts: Iterable[Token]) -> Tuple[NamePart, ...]:
    return tuple(
        part if isinstance(part, NamePart) else NamePart.of(part) for part in parts
    )


def _validate_sub_index(_instance, _attribute, value: Optional[int]) -> None:
    if value is not None and value < 0:
        raise ValueError("Sub-index must be >= 0.")


@attr.s(auto_attribs=True, frozen=True)
class NamedSign(AbstractSign):
    name_parts: NameParts = attr.ib(converter=convert_name_parts)
    sub_index: Optional[int] = attr.ib(default=1, validator=_validate_sub_index)
    sign: Optional[Token] = None

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
