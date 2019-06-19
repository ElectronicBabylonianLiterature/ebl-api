from typing import Iterable, Sequence, Tuple, TypeVar, Callable, Type

import attr
import pydash

from ebl.corpus.alignment import AlignmentToken, AlignmentError
from ebl.merger import Merger
from ebl.text.atf import Atf, WORD_SEPARATOR
from ebl.text.lemmatization import LemmatizationError, LemmatizationToken
from ebl.text.token import Token
from ebl.text.visitors import AtfVisitor, LanguageVisitor
from ebl.text.labels import LineNumberLabel

T = TypeVar('T')


@attr.s(auto_attribs=True, frozen=True)
class Line:
    prefix: str = ''
    content: Tuple[Token, ...] = tuple()

    @property
    def atf(self) -> Atf:
        content = WORD_SEPARATOR.join(
            token.value
            for token in self.content
        )
        return Atf(f'{self.prefix}{content}')

    def update_lemmatization(
            self,
            lemmatization: Sequence[LemmatizationToken]
    ) -> 'Line':
        def updater(token, lemmatization_token):
            return token.set_unique_lemma(lemmatization_token)

        return self._update_tokens(lemmatization, updater, LemmatizationError)

    def update_alignment(
            self,
            alignment: Sequence[AlignmentToken]
    ) -> 'Line':
        def updater(token, alignment_token):
            return token.set_alignment(alignment_token)

        return self._update_tokens(alignment, updater, AlignmentError)

    def _update_tokens(self, updates: Sequence[T],
                       updater: Callable[[Token, T], Token],
                       error_class: Type[Exception]) -> 'Line':
        if len(self.content) == len(updates):
            zipped = pydash.zip_(list(self.content), list(updates))
            content = tuple(
                updater(pair[0], pair[1])
                for pair in zipped
            )
            return attr.evolve(
                self,
                content=content
            )
        else:
            raise error_class()

    def to_dict(self) -> dict:
        return {
            'prefix': self.prefix,
            'content': [token.to_dict() for token in self.content]
        }

    def merge(self, other: 'Line') -> 'Line':
        return other


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content,))

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'ControlLine'
        }


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):

    @classmethod
    def of_iterable(cls,
                    line_number: LineNumberLabel,
                    content: Iterable[Token]):
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

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'TextLine'
        }

    def merge(self, other: 'Line') -> 'Line':
        def merge_tokens():
            def map_(token):
                return f'{type(token)}⋮{token.value}'

            return Merger(map_).merge(self.content, other.content)

        return (
            TextLine.of_iterable(other.line_number, merge_tokens())
            if isinstance(other, TextLine)
            else other
        )


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):

    def to_dict(self) -> dict:
        return {
            'type': 'EmptyLine',
            'prefix': '',
            'content': []
        }
