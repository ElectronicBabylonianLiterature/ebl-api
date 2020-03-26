from typing import List, Sequence

from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.tokens import (
    LanguageShift,
    Token,
    TokenVisitor,
)
from ebl.transliteration.domain.word_tokens import DEFAULT_NORMALIZED, Word


class LanguageVisitor(TokenVisitor):
    def __init__(self):
        self._tokens: List[Token] = []
        self._language: Language = DEFAULT_LANGUAGE
        self._normalized: bool = DEFAULT_NORMALIZED

    @property
    def tokens(self) -> Sequence[Token]:
        return tuple(self._tokens)

    def visit(self, token: Token) -> None:
        self._append(token)

    def visit_language_shift(self, shift: LanguageShift) -> None:
        if shift.language is not Language.UNKNOWN:
            self._language = shift.language
            self._normalized = shift.normalized

        self._append(shift)

    def visit_word(self, word: Word) -> None:
        word_with_language = word.set_language(self._language, self._normalized)
        self._append(word_with_language)

    def _append(self, token: Token) -> None:
        self._tokens.append(token)
