from functools import singledispatchmethod  # type: ignore
from typing import AbstractSet, FrozenSet

import attr

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Enclosure,
    Gloss,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.sign_tokens import NamedSign
from ebl.transliteration.domain.tokens import Token, TokenVisitor, Variant
from ebl.transliteration.domain.word_tokens import Word


@attr.s(auto_attribs=True, frozen=True)
class EnclosureVisitorState:
    enclosures: FrozenSet[EnclosureType] = frozenset()

    @property
    def has_enclosures(self) -> int:
        return len(self.enclosures) > 0

    def is_open(self, enclosure: EnclosureType) -> bool:
        return enclosure in self.enclosures

    def open(self, enclosure: EnclosureType) -> "EnclosureVisitorState":
        if self._is_allowed_to_open(enclosure):
            return EnclosureVisitorState(self.enclosures.union({enclosure}))
        else:
            raise EnclosureError()

    def close(self, enclosure: EnclosureType) -> "EnclosureVisitorState":
        if self._is_allowed_to_close(enclosure):
            return EnclosureVisitorState(self.enclosures.difference({enclosure}))
        else:
            raise EnclosureError()

    def _is_allowed_to_open(self, enclosure: EnclosureType) -> bool:
        return enclosure.does_not_forbid(
            self.enclosures
        ) and enclosure.are_requirements_satisfied_by(self.enclosures)

    def _is_allowed_to_close(self, enclosure: EnclosureType) -> bool:
        return self.is_open(enclosure) and not self._is_required(enclosure)

    def _is_required(self, enclosure: EnclosureType) -> bool:
        required = {
            required_type
            for open_ in self.enclosures
            for required_type in open_.required
        }
        return enclosure in required


@attr.s(auto_attribs=True)
class EnclosureVisitor(TokenVisitor):
    _state: EnclosureVisitorState = EnclosureVisitorState()

    @property
    def enclosures(self) -> AbstractSet[EnclosureType]:
        return self._state.enclosures

    def done(self):
        if self._state.has_enclosures:
            raise EnclosureError()

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        pass

    @visit.register
    def _visit_variant(self, token: Variant) -> None:
        def sub_visit(sub_token: Token) -> AbstractSet[EnclosureType]:
            sub_visitor = EnclosureVisitor(self._state)
            sub_token.accept(sub_visitor)
            return sub_visitor.enclosures

        results = set(map(sub_visit, token.tokens))

        if len(results) == 1:
            self._state = EnclosureVisitorState(frozenset(results.pop()))
        else:
            raise EnclosureError()

    @visit.register
    def _visit_word(self, token: Word) -> None:
        for part in token.parts:
            part.accept(self)

    @visit.register
    def _visit_gloss(self, token: Gloss) -> None:
        for part in token.parts:
            part.accept(self)

    @visit.register
    def _visit_named_sign(self, token: NamedSign) -> None:
        for part in token.name_parts:
            part.accept(self)

    @visit.register
    def _visit_accidental_omission(self, token: AccidentalOmission) -> None:
        self._update_state(token, EnclosureType.ACCIDENTAL_OMISSION)

    @visit.register
    def _visit_intentional_omission(self, token: IntentionalOmission) -> None:
        self._update_state(token, EnclosureType.INTENTIONAL_OMISSION)

    @visit.register
    def _visit_removal(self, token: Removal) -> None:
        self._update_state(token, EnclosureType.REMOVAL)

    @visit.register
    def _visit_broken_away(self, token: BrokenAway) -> None:
        self._update_state(token, EnclosureType.BROKEN_AWAY)

    @visit.register
    def _visit_perhaps_broken_away(self, token: PerhapsBrokenAway) -> None:
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if self._state.is_open(EnclosureType.BROKEN_AWAY)
            else EnclosureType.PERHAPS
        )
        self._update_state(token, perhaps_type)

    @visit.register
    def _visit_document_oriented_gloss(self, token: DocumentOrientedGloss) -> None:
        self._update_state(token, EnclosureType.DOCUMENT_ORIENTED_GLOSS)

    def _update_state(self, token: Enclosure, enclosure: EnclosureType):
        self._state = (
            self._state.open(enclosure)
            if token.is_open
            else self._state.close(enclosure)
        )
