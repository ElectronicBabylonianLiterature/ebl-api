from abc import ABC, abstractmethod
from typing import Callable, Sequence, Tuple, Type, TypeVar

import attr

from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import Token, ValueToken


T = TypeVar("T")
L = TypeVar("L", bound="Line")


@attr.s(frozen=True)
class Line(ABC):
    @property
    @abstractmethod
    def prefix(self) -> str:
        ...

    @property
    @abstractmethod
    def content(self) -> Sequence[Token]:
        ...

    @property
    @abstractmethod
    def atf(self) -> Atf:
        ...

    @property
    def key(self) -> str:
        tokens = "⁚".join(token.get_key() for token in self.content)
        return f"{type(self).__name__}⁞{self.atf}⟨{tokens}⟩"

    def update_lemmatization(
        self, lemmatization: Sequence[LemmatizationToken]
    ) -> "Line":
        def updater(token, lemmatization_token):
            return token.set_unique_lemma(lemmatization_token)

        return self._update_tokens(lemmatization, updater, LemmatizationError)

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "Line":
        return self

    def _update_tokens(
        self: L,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> L:
        return self

    def merge(self, other: L) -> L:
        return other

    def strip_alignments(self: L) -> L:
        return self


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):
    _prefix: str
    _content: str

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def content(self) -> Tuple[ValueToken]:
        return (ValueToken.of(self._content),)

    @property
    def atf(self) -> Atf:
        return Atf(f"{self.prefix}{self._content}")


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    @property
    def prefix(self) -> str:
        return ""

    @property
    def content(self):
        return tuple()

    @property
    def atf(self) -> Atf:
        return Atf("")
