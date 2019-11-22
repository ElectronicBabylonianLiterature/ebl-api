from functools import singledispatchmethod  # type: ignore
from typing import Callable, List, Tuple

from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.enclosure_tokens import Side, \
    DocumentOrientedGloss, BrokenAway, PerhapsBrokenAway, Erasure, \
    OmissionOrRemoval
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.sign_tokens import Divider
from ebl.transliteration.domain.tokens import (LanguageShift,
                                               Token,
                                               TokenVisitor,
                                               CommentaryProtocol)
from ebl.transliteration.domain.word_tokens import DEFAULT_NORMALIZED, Word


class LanguageVisitor(TokenVisitor):
    def __init__(self):
        self._tokens: List[Token] = []
        self._language: Language = DEFAULT_LANGUAGE
        self._normalized: bool = DEFAULT_NORMALIZED

    @property
    def tokens(self) -> Tuple[Token, ...]:
        return tuple(self._tokens)

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        self._append(token)

    @visit.register
    def _visit_language_shift(self, shift: LanguageShift) -> None:
        if shift.language is not Language.UNKNOWN:
            self._language = shift.language
            self._normalized = shift.normalized

        self._append(shift)

    @visit.register
    def _visit_word(self, word: Word) -> None:
        word_with_language =\
            word.set_language(self._language, self._normalized)
        self._append(word_with_language)

    def _append(self, token: Token) -> None:
        self._tokens.append(token)


class AtfVisitor(TokenVisitor):
    def __init__(self, prefix: str):
        self._parts: List[str] = [prefix]
        self._force_separator: bool = True
        self._omit_separator: bool = False

    @property
    def result(self) -> Atf:
        return Atf(''.join(self._parts))

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        if self._force_separator or not self._omit_separator:
            self._append_separator()

        self._parts.append(token.value)
        self._set_omit(False)

    @visit.register
    def _visit_language_shift(self, shift: LanguageShift) -> None:
        self._append_separator()
        self._parts.append(shift.value)
        self._set_force()

    @visit.register
    def _visit_word(self, word: Word) -> None:
        if not self._omit_separator:
            self._append_separator()

        self._parts.append(word.value)
        self._set_omit(False)

    @visit.register
    def _visit_document_oriented_gloss(
            self, gloss: DocumentOrientedGloss
    ) -> None:
        self._side(gloss.side)(gloss)

    @visit.register
    def _visit_broken_away(self, broken_away: BrokenAway) -> None:
        self._side(broken_away.side)(broken_away)

    @visit.register
    def _visit_perhaps_broken_away(self,
                                   broken_away: PerhapsBrokenAway) -> None:
        self._side(broken_away.side)(broken_away)

    @visit.register
    def _visit_omission_or_removal(
            self, omission: OmissionOrRemoval
    ) -> None:
        self._side(omission.side)(omission)

    def _side(self, side: Side) -> Callable[[Token], None]:
        return {
            Side.LEFT: self._left,
            Side.RIGHT: self._right
        }[side]

    def _left(self, token: Token) -> None:
        if not self._omit_separator:
            self._append_separator()
        self._parts.append(token.value)
        self._set_omit(True)

    def _right(self, token: Token) -> None:
        if self._force_separator:
            self._append_separator()
        self._parts.append(token.value)
        self._set_omit(False)

    @visit.register
    def _visit_erasure(self, erasure: Erasure):
        def left():
            self._append_separator()
            self._parts.append(erasure.value)
            self._set_omit(True)

        def center():
            self._parts.append(erasure.value)
            self._set_omit(True)

        def right():
            self._parts.append(erasure.value)
            self._set_force()

        {Side.LEFT: left,
         Side.CENTER: center,
         Side.RIGHT: right}[erasure.side]()

    @visit.register
    def _visit_divider(self, divider: Divider) -> None:
        self._append_separator()
        self._parts.append(divider.value)
        self._set_force()

    @visit.register
    def _visit_commentary_protocol(self, protocol: CommentaryProtocol) -> None:
        self._append_separator()
        self._parts.append(protocol.value)
        self._set_force()

    def _append_separator(self) -> None:
        self._parts.append(WORD_SEPARATOR)

    def _set_omit(self, omit):
        self._omit_separator = omit
        self._force_separator = False

    def _set_force(self):
        self._omit_separator = False
        self._force_separator = True
