from typing import Callable, List, Optional, Sequence

from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Erasure,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import Divider
from ebl.transliteration.domain.tokens import (
    CommentaryProtocol,
    LanguageShift,
    LineBreak,
    Token,
    TokenVisitor,
)
from ebl.transliteration.domain.word_tokens import Word


class AtfVisitor(TokenVisitor):
    def __init__(self, prefix: Optional[str]):
        self._parts: List[str] = [] if prefix is None else [prefix]
        self._force_separator: bool = prefix is not None
        self._omit_separator: bool = prefix is None

    @property
    def result(self) -> Atf:
        return Atf("".join(self._parts))

    def visit(self, token: Token) -> None:
        if self._force_separator or not self._omit_separator:
            self._append_separator()

        self._parts.append(token.value)
        self._set_omit(False)

    def visit_language_shift(self, shift: LanguageShift) -> None:
        self._append_separator()
        self._parts.append(shift.value)
        self._set_force()

    def visit_word(self, word: Word) -> None:
        if not self._omit_separator:
            self._append_separator()

        self._parts.append(word.value)
        self._set_omit(False)

    def visit_document_oriented_gloss(self, gloss: DocumentOrientedGloss) -> None:
        self._side(gloss.side)(gloss)

    def visit_broken_away(self, broken_away: BrokenAway) -> None:
        self._side(broken_away.side)(broken_away)

    def visit_perhaps_broken_away(self, broken_away: PerhapsBrokenAway) -> None:
        self._side(broken_away.side)(broken_away)

    def visit_omission(self, omission: AccidentalOmission) -> None:
        self._side(omission.side)(omission)

    def visit_accidental_omission(self, omission: IntentionalOmission) -> None:
        self._side(omission.side)(omission)

    def visit_removal(self, removal: Removal) -> None:
        self._side(removal.side)(removal)

    def _side(self, side: Side) -> Callable[[Token], None]:
        return {Side.LEFT: self._left, Side.RIGHT: self._right}[side]

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

    def visit_erasure(self, erasure: Erasure):
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

        {Side.LEFT: left, Side.CENTER: center, Side.RIGHT: right}[erasure.side]()

    def visit_divider(self, divider: Divider) -> None:
        self._append_separator()
        self._parts.append(divider.value)
        self._set_force()

    def visit_line_break(self, line_break: LineBreak) -> None:
        self._append_separator()
        self._parts.append(line_break.value)
        self._set_force()

    def visit_commentary_protocol(self, protocol: CommentaryProtocol) -> None:
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


def convert_to_atf(prefix: Optional[str], tokens: Sequence[Token]) -> Atf:
    visitor = AtfVisitor(prefix)
    for token in tokens:
        token.accept(visitor)
    return visitor.result
