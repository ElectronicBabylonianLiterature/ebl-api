from abc import ABC, abstractmethod
from typing import Callable, Sequence, Type, TypeVar

import attr

from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import Token


@attr.s(auto_attribs=True, frozen=True)
class Line(ABC):
    T = TypeVar("T")

    @property
    @abstractmethod
    def prefix(self) -> str:
        ...

    @property
    @abstractmethod
    def content(self) -> Sequence[Token]:
        ...

    @property
    def key(self) -> str:
        tokens = [token.get_key() for token in self.content]
        return "⁞".join([str(self.atf)] + tokens)

    @property
    def atf(self) -> Atf:
        content = WORD_SEPARATOR.join(token.value for token in self.content)
        return Atf(f"{self.prefix}{content}")

    def update_lemmatization(
        self, lemmatization: Sequence[LemmatizationToken]
    ) -> "Line":
        def updater(token, lemmatization_token):
            return token.set_unique_lemma(lemmatization_token)

        return self._update_tokens(lemmatization, updater, LemmatizationError)

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "Line":
        return self

    def _update_tokens(
        self,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> "Line":
        return self

    def merge(self, other: "Line") -> "Line":
        return other

    def strip_alignments(self):
        return self


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):
    _prefix: str = ""
    _content: Sequence[Token] = tuple()

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content,))

    @property
    def prefix(self):
        return self._prefix

    @property
    def content(self):
        return self._content


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    @property
    def prefix(self):
        return ""

    @property
    def content(self):
        return tuple()
