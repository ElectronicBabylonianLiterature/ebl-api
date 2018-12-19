# pylint: disable=R0903
from typing import Any, List, Tuple, NewType, Iterable
import attr
from ebl.fragmentarium.language import Language


DEFAULT_LANGUAGE = Language.AKKADIAN
UniqueLemma = NewType('UniqueLemma', str)


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False

    def accept(self, visitor: Any) -> None:
        visitor.visit_token(self)


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = Language.AKKADIAN
    unique_lemma: Tuple[UniqueLemma, ...] = tuple()

    @property
    def lemmatizable(self) -> bool:
        return self.language.lemmatizable

    def set_language(self, language: Language) -> 'Word':
        return attr.evolve(self, language=language)

    def accept(self, visitor: Any) -> None:
        visitor.visit_word(self)


@attr.s(auto_attribs=True, frozen=True)
class LanguageShift(Token):
    language: Language = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, 'language', Language.of_atf(self.value))

    def accept(self, visitor: Any) -> None:
        visitor.visit_language_shift(self)


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
