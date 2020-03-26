from typing import FrozenSet, List, Sequence

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
class EnclosureValidator(TokenVisitor):
    _state: EnclosureVisitorState = EnclosureVisitorState()

    @property
    def enclosures(self) -> FrozenSet[EnclosureType]:
        return self._state.enclosures

    def done(self):
        if self._state.has_enclosures:
            raise EnclosureError()

    def visit_variant(self, token: Variant) -> None:
        def sub_visit(sub_token: Token) -> FrozenSet[EnclosureType]:
            sub_visitor = EnclosureValidator(self._state)
            sub_token.accept(sub_visitor)
            return sub_visitor.enclosures

        results = set(map(sub_visit, token.tokens))

        if len(results) == 1:
            self._state = EnclosureVisitorState(frozenset(results.pop()))
        else:
            raise EnclosureError()

    def visit_word(self, token: Word) -> None:
        for part in token.parts:
            part.accept(self)

    def visit_gloss(self, token: Gloss) -> None:
        for part in token.parts:
            part.accept(self)

    def visit_named_sign(self, token: NamedSign) -> None:
        for part in token.name_parts:
            part.accept(self)

    def visit_accidental_omission(self, token: AccidentalOmission) -> None:
        self._update_state(token, EnclosureType.ACCIDENTAL_OMISSION)

    def visit_intentional_omission(self, token: IntentionalOmission) -> None:
        self._update_state(token, EnclosureType.INTENTIONAL_OMISSION)

    def visit_removal(self, token: Removal) -> None:
        self._update_state(token, EnclosureType.REMOVAL)

    def visit_broken_away(self, token: BrokenAway) -> None:
        self._update_state(token, EnclosureType.BROKEN_AWAY)

    def visit_perhaps_broken_away(self, token: PerhapsBrokenAway) -> None:
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if self._state.is_open(EnclosureType.BROKEN_AWAY)
            else EnclosureType.PERHAPS
        )
        self._update_state(token, perhaps_type)

    def visit_document_oriented_gloss(self, token: DocumentOrientedGloss) -> None:
        self._update_state(token, EnclosureType.DOCUMENT_ORIENTED_GLOSS)

    def _update_state(self, token: Enclosure, enclosure: EnclosureType):
        self._state = (
            self._state.open(enclosure)
            if token.is_open
            else self._state.close(enclosure)
        )


@attr.s(auto_attribs=True)
class EnclosureUpdater(TokenVisitor):
    _enclosures: FrozenSet[EnclosureType] = frozenset()
    _tokens: List[Token] = attr.ib(factory=list)

    @property
    def tokens(self) -> Sequence[Token]:
        return tuple(self._tokens)

    def _set_enclosure_type(self, token: Token) -> Token:
        return token.set_enclosure_type(self._enclosures)

    def _append_token(self, token: Token) -> None:
        self._tokens.append(token)

    def visit(self, token: Token) -> None:
        self._append_token(self._set_enclosure_type(token))

    def visit_variant(self, token: Variant) -> None:
        def sub_visit(sub_token: Token) -> EnclosureUpdater:
            sub_visitor = EnclosureUpdater(self._enclosures)
            sub_token.accept(sub_visitor)
            return sub_visitor

        new_token = self._set_enclosure_type(token)
        visitors = list(map(sub_visit, token.tokens))

        enclosures = set(visitor._enclosures for visitor in visitors)
        self._enclosures = sorted(enclosures, key=len, reverse=True)[0]

        tokens = tuple(token for visitor in visitors for token in visitor.tokens)
        self._append_token(attr.evolve(new_token, tokens=tokens))

    def visit_word(self, token: Word) -> None:
        new_token = self._set_enclosure_type(token)
        visited_parts = self._visit_parts(token.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_named_sign(self, token: NamedSign) -> None:
        new_token = self._set_enclosure_type(token)
        visited_parts: Sequence = self._visit_parts(token.name_parts)
        self._append_token(attr.evolve(new_token, name_parts=visited_parts))

    def visit_gloss(self, token: Gloss) -> None:
        new_token = self._set_enclosure_type(token)
        visited_parts = self._visit_parts(token.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_accidental_omission(
        self, token: None
    ) -> None:
        new_token = self._set_enclosure_type(token)
        self._update_enclosures(token, EnclosureType.ACCIDENTAL_OMISSION)
        self._append_token(new_token)

    def visit_intentional_omission(
        self, token: IntentionalOmission
    ) -> None:
        new_token = self._set_enclosure_type(token)
        self._update_enclosures(token, EnclosureType.INTENTIONAL_OMISSION)
        self._append_token(new_token)

    def visit_removal(self, token: Removal) -> None:
        new_token = self._set_enclosure_type(token)
        self._update_enclosures(token, EnclosureType.REMOVAL)
        self._append_token(new_token)

    def visit_broken_away(self, token: BrokenAway) -> BrokenAway:
        new_token = self._set_enclosure_type(token)
        self._update_enclosures(token, EnclosureType.BROKEN_AWAY)
        self._append_token(new_token)

    def visit_perhaps_broken_away(self, token: PerhapsBrokenAway) -> None:
        new_token = self._set_enclosure_type(token)
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if EnclosureType.BROKEN_AWAY in self._enclosures
            else EnclosureType.PERHAPS
        )
        self._update_enclosures(token, perhaps_type)
        self._append_token(new_token)

    def visit_document_oriented_gloss(
        self, token: DocumentOrientedGloss
    ) -> None:
        new_token = self._set_enclosure_type(token)
        self._update_enclosures(token, EnclosureType.DOCUMENT_ORIENTED_GLOSS)
        self._append_token(new_token)

    def _visit_parts(self, tokens: Sequence[Token]) -> Sequence[Token]:
        part_visitor = EnclosureUpdater(self._enclosures)
        for token in tokens:
            token.accept(part_visitor)

        self._enclosures = part_visitor._enclosures

        return part_visitor.tokens

    def _update_enclosures(self, token: Enclosure, enclosure: EnclosureType):
        self._enclosures = (
            self._enclosures.union({enclosure})
            if token.is_open
            else self._enclosures.difference({enclosure})
        )
