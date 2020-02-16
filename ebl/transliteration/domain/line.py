from abc import ABC, abstractmethod
from typing import Callable, Iterable, Sequence, Tuple, Type, TypeVar

import attr
import pydash

from ebl.merger import Merger
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.atf_visitor import AtfVisitor
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language_visitor import LanguageVisitor
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import Token

T = TypeVar("T")
L = TypeVar("L", "TextLine", "Line")


@attr.s(auto_attribs=True, frozen=True)
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
class TextLine(Line):
    _prefix: str = ""
    _content: Sequence[Token] = tuple()

    @property
    def prefix(self):
        return self._prefix

    @property
    def content(self):
        return self._content

    @classmethod
    def of_iterable(cls, line_number: LineNumberLabel, content: Iterable[Token]):
        visitor = LanguageVisitor()
        for token in content:
            token.accept(visitor)
        return cls(line_number.to_atf(), visitor.tokens)

    @property
    def line_number(self) -> LineNumberLabel:
        return LineNumberLabel.from_atf(self.prefix)

    @property
    def atf(self) -> Atf:
        visitor = AtfVisitor(self.prefix)
        for token in self.content:
            token.accept(visitor)
        return visitor.result

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "Line":
        def updater(token, alignment_token):
            return token.set_alignment(alignment_token)

        return self._update_tokens(alignment, updater, AlignmentError)

    def _update_tokens(
        self,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> "Line":
        if len(self.content) == len(updates):
            zipped = pydash.zip_(list(self.content), list(updates))
            content = tuple(updater(pair[0], pair[1]) for pair in zipped)
            return attr.evolve(self, content=content)
        else:
            raise error_class()

    def merge(self, other: L) -> L:
        def merge_tokens():
            def map_(token):
                return token.get_key()

            def inner_merge(old: Token, new: Token) -> Token:
                return old.merge(new)

            return Merger(map_, inner_merge).merge(self.content, other.content)

        return (
            TextLine.of_iterable(other.line_number, merge_tokens())
            if isinstance(other, TextLine)
            else other
        )

    def strip_alignments(self) -> "TextLine":
        stripped_content = tuple(token.strip_alignment() for token in self.content)
        return attr.evolve(self, content=stripped_content)


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    @property
    def prefix(self):
        return ""

    @property
    def content(self):
        return tuple()
