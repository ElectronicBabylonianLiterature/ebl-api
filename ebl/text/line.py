# pylint: disable=R0903
from typing import List, Tuple, Iterable, Sequence
import attr
import pydash
from ebl.merger import Merger
from ebl.text.atf import Atf
from ebl.text.language import Language, DEFAULT_LANGUAGE
from ebl.text.lemmatization import LemmatizationToken, LemmatizationError
from ebl.text.token import (
    Token, Word, LanguageShift, DocumentOrientedGloss, Side, DEFAULT_NORMALIZED
)


WORD_SEPARATOR = ' '


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

    class LanguageVisitor:
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

        def visit_document_oriented_gloss(
                self, gloss: DocumentOrientedGloss
        ) -> None:
            self.visit_token(gloss)

    class AtfVisitor:
        def __init__(self, prefix: str):
            self._parts: List[str] = [prefix]
            self._force_separator: bool = True
            self._omit_separator: bool = False

        @property
        def result(self) -> Atf:
            return Atf(''.join(self._parts))

        def visit_token(self, token: Token) -> None:
            if self._force_separator or not self._omit_separator:
                self._append_separator()

            self._parts.append(token.value)
            self._set_omit(False)

        def visit_language_shift(self, shift: LanguageShift) -> None:
            self._append_separator()
            self._parts.append(shift.value)
            self._set_force()

        def visit_word(self, word: Word) -> None:
            should_not_omit = not(self._omit_separator or word.partial.start)
            if (self._force_separator or should_not_omit):
                self._append_separator()

            self._parts.append(word.value)
            self._set_omit(word.partial.end)

        def visit_document_oriented_gloss(
                self, gloss: DocumentOrientedGloss
        ) -> None:
            def left():
                self._append_separator()
                self._parts.append(gloss.value)
                self._set_omit(True)

            def right():
                if self._force_separator:
                    self._append_separator()
                self._parts.append(gloss.value)
                self._set_force()

            {Side.LEFT: left, Side.RIGHT: right}[gloss.side]()

        def _append_separator(self) -> None:
            self._parts.append(WORD_SEPARATOR)

        def _set_omit(self, omit):
            self._omit_separator = omit
            self._force_separator = False

        def _set_force(self):
            self._omit_separator = False
            self._force_separator = True

    @classmethod
    def of_iterable(cls, prefix: str, content: Iterable[Token]):
        visitor = cls.LanguageVisitor()
        for token in content:
            token.accept(visitor)
        return cls(prefix, visitor.tokens)

    @property
    def atf(self) -> Atf:
        visitor = TextLine.AtfVisitor(self.prefix)
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
