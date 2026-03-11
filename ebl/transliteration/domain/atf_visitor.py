from typing import Callable, List, Optional, Sequence

from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Erasure,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
    Emendation,
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


class AtfVisitorState:
    def __init__(self, prefix: Optional[str]):
        self.parts: List[str] = [] if prefix is None else [prefix]
        self._force_separator: bool = prefix is not None
        self._omit_separator: bool = prefix is None

    def append_with_forced_separator(self, token: Token) -> None:
        self.append_separator()
        self.append_token(token)
        self.set_force()

    def append_with_separator(self, token: Token) -> None:
        if self._force_separator or not self._omit_separator:
            self.append_separator()

        self.append_token(token)
        self.set_omit(False)

    def append_left_bracket(self, token: Token) -> None:
        if not self._omit_separator:
            self.append_separator()
        self.append_token(token)
        self.set_omit(True)

    def append_right_bracket(self, token: Token) -> None:
        if self._force_separator:
            self.append_separator()
        self.append_token(token)
        self.set_omit(False)

    def append_token(self, token: Token) -> None:
        self.parts.append(token.value)

    def append_separator(self) -> None:
        self.parts.append(WORD_SEPARATOR)

    def set_omit(self, omit: bool) -> None:
        self._omit_separator = omit
        self._force_separator = False

    def set_force(self) -> None:
        self._omit_separator = False
        self._force_separator = True


class AtfVisitor(TokenVisitor):
    def __init__(self, prefix: Optional[str]):
        self._state = AtfVisitorState(prefix)

    @property
    def result(self) -> Atf:
        return Atf("".join(self._state.parts).strip())

    def visit(self, token: Token) -> None:
        self._state.append_with_separator(token)

    def visit_language_shift(self, shift: LanguageShift) -> None:
        self._state.append_with_forced_separator(shift)

    def visit_word(self, word: Word) -> None:
        self._state.append_with_separator(word)

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

    def visit_emendation(self, emendation: Emendation) -> None:
        self._side(emendation.side)(emendation)

    def _side(self, side: Side) -> Callable[[Token], None]:
        return {
            Side.LEFT: self._state.append_left_bracket,
            Side.RIGHT: self._state.append_right_bracket,
        }[side]

    def visit_erasure(self, erasure: Erasure):
        def left():
            self._state.append_separator()
            self._state.append_token(erasure)
            self._state.set_omit(True)

        def center():
            self._state.append_token(erasure)
            self._state.set_omit(True)

        def right():
            self._state.append_token(erasure)
            self._state.set_force()

        {Side.LEFT: left, Side.CENTER: center, Side.RIGHT: right}[erasure.side]()

    def visit_divider(self, divider: Divider) -> None:
        self._state.append_with_forced_separator(divider)

    def visit_line_break(self, line_break: LineBreak) -> None:
        self._state.append_with_forced_separator(line_break)

    def visit_egyptian_metrical_feet_separator(
        self, egyptian_metrical_feet_separator: EgyptianMetricalFeetSeparator
    ) -> None:
        self._state.append_with_forced_separator(egyptian_metrical_feet_separator)

    def visit_commentary_protocol(self, protocol: CommentaryProtocol) -> None:
        self._state.append_with_forced_separator(protocol)


def convert_to_atf(prefix: Optional[str], tokens: Sequence[Token]) -> Atf:
    visitor = AtfVisitor(prefix)
    for token in tokens:
        token.accept(visitor)
    return visitor.result
