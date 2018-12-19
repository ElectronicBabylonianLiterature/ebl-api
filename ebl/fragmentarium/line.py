# pylint: disable=R0903
from typing import List, Tuple, Iterable
import attr
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE
from ebl.fragmentarium.token import Token, Word, LanguageShift


@attr.s(auto_attribs=True, frozen=True)
class Line:
    prefix: str = ''
    content: Tuple[Token, ...] = tuple()


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content, ))


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):

    class TokenVisitor:
        def __init__(self):
            self._tokens: List[Token] = []
            self._language: Language = DEFAULT_LANGUAGE

        @property
        def tokens(self) -> Tuple[Token, ...]:
            return tuple(self._tokens)

        def visit_token(self, token: Token) -> None:
            self._tokens.append(token)

        def visit_language_shift(self, shift: LanguageShift) -> None:
            if shift.language is not Language.UNKNOWN:
                self._language = shift.language

            self.visit_token(shift)

        def visit_word(self, word: Word) -> None:
            word_with_language = word.set_language(self._language)
            self.visit_token(word_with_language)

    @classmethod
    def of_iterable(cls, prefix: str, content: Iterable[Token]):
        visitor = cls.TokenVisitor()
        for token in content:
            token.accept(visitor)
        return cls(prefix, visitor.tokens)


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    pass
