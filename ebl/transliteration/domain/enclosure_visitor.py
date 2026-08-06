from typing import FrozenSet

import attr

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Emendation,
    Enclosure,
    Gloss,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.greek_tokens import GreekWord
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import NamedSign
from ebl.transliteration.domain.tokens import Token, TokenVisitor, Variant
from ebl.transliteration.domain.word_tokens import Word

from ebl.transliteration.domain.enclosure_state import EnclosureVisitorState
from ebl.transliteration.domain.enclosure_updater import (
    EnclosureUpdater,
    set_enclosure_type,
)

__all__ = [
    "EnclosureUpdater",
    "EnclosureValidator",
    "EnclosureVisitorState",
    "set_enclosure_type",
]


@attr.s(auto_attribs=True)
class EnclosureValidator(TokenVisitor):
    _state: EnclosureVisitorState = EnclosureVisitorState()

    @property
    def enclosures(self) -> FrozenSet[EnclosureType]:
        return self._state.enclosures

    def done(self):
        if self._state.has_enclosures:
            raise EnclosureError()

    def visit_variant(self, variant: Variant) -> None:
        def sub_visit(sub_token: Token) -> FrozenSet[EnclosureType]:
            sub_visitor = EnclosureValidator(self._state)
            sub_token.accept(sub_visitor)
            return sub_visitor.enclosures

        results = set(map(sub_visit, variant.tokens))

        if len(results) == 1:
            self._state = EnclosureVisitorState(frozenset(results.pop()))
        else:
            raise EnclosureError()

    def visit_word(self, word: Word) -> None:
        for part in word.parts:
            part.accept(self)

    def visit_gloss(self, gloss: Gloss) -> None:
        for part in gloss.parts:
            part.accept(self)

    def visit_named_sign(self, named_sign: NamedSign) -> None:
        for part in named_sign.name_parts:
            part.accept(self)

    def visit_akkadian_word(self, word: AkkadianWord) -> None:
        for part in word.parts:
            part.accept(self)

    def visit_greek_word(self, word: GreekWord) -> None:
        for part in word.parts:
            part.accept(self)

    def visit_accidental_omission(self, omission: AccidentalOmission) -> None:
        self._update_state(omission, EnclosureType.ACCIDENTAL_OMISSION)

    def visit_intentional_omission(self, omission: IntentionalOmission) -> None:
        self._update_state(omission, EnclosureType.INTENTIONAL_OMISSION)

    def visit_removal(self, removal: Removal) -> None:
        self._update_state(removal, EnclosureType.REMOVAL)

    def visit_broken_away(self, broken_away: BrokenAway) -> None:
        self._update_state(broken_away, EnclosureType.BROKEN_AWAY)

    def visit_perhaps_broken_away(self, broken_away: PerhapsBrokenAway) -> None:
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if self._state.is_open(EnclosureType.BROKEN_AWAY)
            else EnclosureType.PERHAPS
        )
        self._update_state(broken_away, perhaps_type)

    def visit_emendation(self, emendation: Emendation) -> None:
        self._update_state(emendation, EnclosureType.EMENDATION)

    def visit_document_oriented_gloss(self, gloss: DocumentOrientedGloss) -> None:
        self._update_state(gloss, EnclosureType.DOCUMENT_ORIENTED_GLOSS)

    def _update_state(self, token: Enclosure, enclosure: EnclosureType):
        self._state = (
            self._state.open(enclosure)
            if token.is_open
            else self._state.close(enclosure)
        )
