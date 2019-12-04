from abc import ABC, abstractmethod
from typing import Iterable, Optional, Sequence, Tuple

import attr

import ebl.transliteration.domain.atf as atf
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)


class TokenVisitor(ABC):
    @abstractmethod
    def visit(self, token: "Token") -> None:
        ...


def convert_token_sequence(tokens: Iterable["Token"]) -> Tuple["Token", ...]:
    return tuple(tokens)


class Token(ABC):
    @property
    @abstractmethod
    def value(self) -> str:
        ...

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def alignable(self) -> bool:
        return self.lemmatizable

    @property
    def parts(self) -> Sequence["Token"]:
        return tuple()

    def get_key(self) -> str:
        parts = (
            f"⟨{'⁚'.join(part.get_key() for part in self.parts)}⟩" if self.parts else ""
        )
        return f"{type(self).__name__}⁝{self.value}{parts}"

    def set_unique_lemma(self, lemma: LemmatizationToken) -> "Token":
        if lemma.unique_lemma is None and lemma.value == self.value:
            return self
        else:
            raise LemmatizationError()

    def set_alignment(self, alignment: AlignmentToken):
        if alignment.alignment is None and alignment.value == self.value:
            return self
        else:
            raise AlignmentError()

    def strip_alignment(self):
        return self

    def merge(self, token: "Token") -> "Token":
        return token

    def accept(self, visitor: "TokenVisitor") -> None:
        visitor.visit(self)


@attr.s(auto_attribs=True, frozen=True)
class ValueToken(Token):
    _value: str

    @property
    def value(self) -> str:
        return self._value


@attr.s(frozen=True)
class LanguageShift(ValueToken):
    _normalization_shift = "%n"

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift


@attr.s(frozen=True)
class UnknownNumberOfSigns(Token):
    @property
    def value(self) -> str:
        return atf.UNKNOWN_NUMBER_OF_SIGNS


@attr.s(frozen=True)
class Tabulation(ValueToken):
    pass


@attr.s(frozen=True)
class CommentaryProtocol(ValueToken):
    @property
    def protocol(self):
        return atf.CommentaryProtocol(self.value)


@attr.s(frozen=True, auto_attribs=True)
class Column(Token):
    number: Optional[int] = attr.ib(default=None)

    @number.validator
    def _check_number(self, _, value) -> None:
        if value is not None and value < 0:
            raise ValueError("number must not be negative")

    @property
    def value(self) -> str:
        return "&" if self.number is None else f"&{self.number}"


@attr.s(frozen=True, auto_attribs=True)
class Variant(Token):
    tokens: Tuple[Token, ...]

    @staticmethod
    def of(first: Token, second: Token) -> "Variant":
        return Variant((first, second))

    @property
    def value(self) -> str:
        return "/".join(token.value for token in self.tokens)


@attr.s(frozen=True)
class LineContinuation(ValueToken):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Joiner(Token):
    _value: atf.Joiner

    @property
    def value(self):
        return self._value.value

    @staticmethod
    def dot():
        return Joiner(atf.Joiner.DOT)

    @staticmethod
    def hyphen():
        return Joiner(atf.Joiner.HYPHEN)

    @staticmethod
    def colon():
        return Joiner(atf.Joiner.COLON)

    @staticmethod
    def plus():
        return Joiner(atf.Joiner.PLUS)
