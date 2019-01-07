# pylint: disable=R0903
from typing import List, Tuple, Iterable, Sequence
import attr
import pydash
from ebl.merger import Merger
from ebl.text.atf import Atf
from ebl.text.language import Language, DEFAULT_LANGUAGE
from ebl.text.lemmatization import LemmatizationToken, LemmatizationError
from ebl.text.token import (
    Token, Word, LanguageShift, DEFAULT_NORMALIZED
)


@attr.s(auto_attribs=True, frozen=True)
class Line:
    prefix: str = ''
    content: Tuple[Token, ...] = tuple()

    @property
    def atf(self) -> Atf:
        return Atf(f'{self.prefix}{self._join_content()}')

    def _join_content(self) -> str:
        return ' '.join(
            token.value
            for token in self.content
        )

    def update_lemmatization(
            self,
            lemmatization: Sequence[LemmatizationToken]
    ) -> 'Line':
        if len(self.content) == len(lemmatization):
            zipped = pydash.zip_(self.content, lemmatization)
            content = tuple(
                pair[0].set_unique_lemma(pair[1])
                for pair in zipped
            )
            return attr.evolve(
                self,
                content=content
            )
        else:
            raise LemmatizationError()

    def to_dict(self) -> dict:
        return {
            'prefix': self.prefix,
            'content': [token.to_dict() for token in self.content]
        }

    def merge(self, other: 'Line') -> 'Line':
        # pylint: disable=R0201
        return other


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content, ))

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'ControlLine'
        }


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):

    class TokenVisitor:
        def __init__(self):
            self._tokens: List[Token] = []
            self._language: Language = DEFAULT_LANGUAGE
            self._normalized: bool = DEFAULT_NORMALIZED

        @property
        def tokens(self) -> Tuple[Token, ...]:
            return tuple(self._tokens)

        def visit_token(self, token: Token) -> None:
            self._tokens.append(token)

        def visit_language_shift(self, shift: LanguageShift) -> None:
            if shift.language is not Language.UNKNOWN:
                self._language = shift.language
                self._normalized = shift.normalized

            self.visit_token(shift)

        def visit_word(self, word: Word) -> None:
            word_with_language =\
                word.set_language(self._language, self._normalized)
            self.visit_token(word_with_language)

    @classmethod
    def of_iterable(cls, prefix: str, content: Iterable[Token]):
        visitor = cls.TokenVisitor()
        for token in content:
            token.accept(visitor)
        return cls(prefix, visitor.tokens)

    @property
    def atf(self) -> Atf:
        return Atf(f'{self.prefix} {self._join_content()}')

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'TextLine'
        }

    def merge(self, other: 'Line') -> 'Line':
        def merge_tokens():
            return Merger(lambda token: token.value).merge(
                self.content, other.content
            )

        return (
            TextLine.of_iterable(other.prefix, merge_tokens())
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
