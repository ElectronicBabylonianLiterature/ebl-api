from itertools import zip_longest
from typing import Callable, Iterable, Sequence, Type, TypeVar, Union, cast

import attr
import pydash

from ebl.merger import Merger
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.tokens import Token, TokenVisitor
from ebl.transliteration.domain.word_tokens import Word

L = TypeVar("L", "TextLine", "Line")
T = TypeVar("T")


def update_tokens(
    tokens: Sequence[Token],
    updates: Sequence[T],
    updater: Callable[[Token, T], Token],
    error_class: Type[Exception],
) -> Sequence[Token]:
    if len(tokens) != len(updates):
        raise error_class()

    zipped = zip_longest(tokens, updates)
    return tuple(updater(pair[0], pair[1]) for pair in zipped)


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):
    line_number: AbstractLineNumber
    _content: Sequence[Token] = tuple()

    @property
    def key(self) -> str:
        tokens = "⁚".join(token.get_key() for token in self.content)
        return f"{type(self).__name__}⁞{self.atf}⟨{tokens}⟩"

    @property
    def content(self) -> Sequence[Token]:
        return self._content

    @staticmethod
    def of_iterable(
        line_number: AbstractLineNumber, content: Iterable[Token]
    ) -> "TextLine":
        return TextLine(
            line_number, pydash.flow(set_enclosure_type, set_language)(content)
        )

    @property
    def atf(self) -> Atf:
        return convert_to_atf(self.line_number.atf, self.content)

    @property
    def lemmatization(self) -> Sequence[LemmatizationToken]:
        return tuple(
            (
                LemmatizationToken(token.value, token.unique_lemma)
                if isinstance(token, Word)
                else LemmatizationToken(token.value)
            )
            for token in self.content
        )

    def update_lemmatization(
        self, lemmatization: Sequence[LemmatizationToken]
    ) -> "TextLine":
        def updater(token, lemmatization_token):
            return token.set_unique_lemma(lemmatization_token)

        return self._update_tokens(lemmatization, updater, LemmatizationError)

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "TextLine":
        def updater(token, alignment_token):
            return alignment_token.apply(token)

        return self._update_tokens(alignment, updater, AlignmentError)

    def _update_tokens(
        self,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> "TextLine":
        return attr.evolve(
            self, content=update_tokens(self.content, updates, updater, error_class)
        )

    def merge(self, other: L) -> Union["TextLine", L]:
        def merge_tokens():
            def map_(token):
                return token.get_key()

            def inner_merge(old: Token, new: Token) -> Token:
                return old.merge(new)

            return Merger(map_, inner_merge).merge(self.content, other.content)

        return (
            TextLine.of_iterable(cast(TextLine, other).line_number, merge_tokens())
            if isinstance(other, TextLine)
            else other
        )

    def strip_alignments(self) -> "TextLine":
        stripped_content = tuple(token.strip_alignment() for token in self.content)
        return attr.evolve(self, content=stripped_content)

    def accept(self, visitor: TokenVisitor) -> None:
        for token in self.content:
            token.accept(visitor)
