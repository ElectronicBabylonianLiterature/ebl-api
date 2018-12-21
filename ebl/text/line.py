# pylint: disable=R0903
from typing import List, Tuple, Iterable
import attr
from ebl.text.language import Language, DEFAULT_LANGUAGE
from ebl.text.token import (
    Token, Word, LanguageShift, DEFAULT_NORMALIZED
)


@attr.s(auto_attribs=True, frozen=True)
class Line:
    prefix: str = ''
    content: Tuple[Token, ...] = tuple()

    def to_dict(self) -> dict:
        return {
            'prefix': self.prefix,
            'content': [token.to_dict() for token in self.content]
        }


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

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'TextLine'
        }


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):

    def to_dict(self) -> dict:
        return {
            'type': 'EmptyLine',
            'prefix': '',
            'content': []
        }
