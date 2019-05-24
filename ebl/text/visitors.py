from typing import List, Tuple

from ebl.text.atf import Atf, WORD_SEPARATOR
from ebl.text.language import DEFAULT_LANGUAGE, Language
from ebl.text.token import (DEFAULT_NORMALIZED, DocumentOrientedGloss, Erasure,
                            LanguageShift, Side, Token, TokenVisitor, Word)


class LanguageVisitor(TokenVisitor):
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

    def visit_erasure(self, erasure: Erasure):
        pass


class AtfVisitor(TokenVisitor):
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

    def visit_erasure(self, erasure: Erasure):
        pass

    def _append_separator(self) -> None:
        self._parts.append(WORD_SEPARATOR)

    def _set_omit(self, omit):
        self._omit_separator = omit
        self._force_separator = False

    def _set_force(self):
        self._omit_separator = False
        self._force_separator = True
