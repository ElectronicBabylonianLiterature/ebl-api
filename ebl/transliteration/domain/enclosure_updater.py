from typing import FrozenSet, Iterable, List, Sequence, TypeVar, Union

import attr

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


TokenT = TypeVar("TokenT", bound=Token)


@attr.s(auto_attribs=True)
class EnclosureUpdater(TokenVisitor):
    _enclosures: FrozenSet[EnclosureType] = frozenset()
    _tokens: List[Token] = attr.ib(factory=list)

    @property
    def tokens(self) -> Sequence[Token]:
        return tuple(self._tokens)

    def _set_enclosure_type(self, token: TokenT) -> TokenT:
        return token.set_enclosure_type(self._enclosures)

    def _append_token(self, token: Token) -> None:
        self._tokens.append(token)

    def visit(self, token: Token) -> None:
        self._append_token(self._set_enclosure_type(token))

    def visit_variant(self, variant: Variant) -> None:
        def sub_visit(sub_token: Token) -> EnclosureUpdater:
            sub_visitor = EnclosureUpdater(self._enclosures)
            sub_token.accept(sub_visitor)
            return sub_visitor

        new_token = self._set_enclosure_type(variant)
        visitors = list(map(sub_visit, variant.tokens))

        enclosures = {visitor._enclosures for visitor in visitors}
        self._enclosures = sorted(enclosures, key=len, reverse=True)[0]

        tokens = tuple(token for visitor in visitors for token in visitor.tokens)
        self._append_token(attr.evolve(new_token, tokens=tokens))

    def visit_word(self, word: Word) -> None:
        new_token = self._set_enclosure_type(word)
        visited_parts = self._visit_parts(word.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_named_sign(self, named_sign: NamedSign) -> None:
        new_token = self._set_enclosure_type(named_sign)
        visited_parts: Sequence = self._visit_parts(named_sign.name_tokens)
        self._append_token(attr.evolve(new_token, name_parts=visited_parts))

    def visit_akkadian_word(self, word: AkkadianWord) -> None:
        new_token = self._set_enclosure_type(word)
        visited_parts: Sequence = self._visit_parts(word.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_greek_word(self, word: GreekWord) -> None:
        new_token = self._set_enclosure_type(word)
        visited_parts: Sequence = self._visit_parts(word.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_gloss(self, gloss: Gloss) -> None:
        new_token = self._set_enclosure_type(gloss)
        visited_parts = self._visit_parts(gloss.parts)
        self._append_token(attr.evolve(new_token, parts=visited_parts))

    def visit_accidental_omission(self, omission: AccidentalOmission) -> None:
        new_token = self._set_enclosure_type(omission)
        self._update_enclosures(omission, EnclosureType.ACCIDENTAL_OMISSION)
        self._append_token(new_token)

    def visit_intentional_omission(self, omission: IntentionalOmission) -> None:
        new_token = self._set_enclosure_type(omission)
        self._update_enclosures(omission, EnclosureType.INTENTIONAL_OMISSION)
        self._append_token(new_token)

    def visit_removal(self, removal: Removal) -> None:
        new_token = self._set_enclosure_type(removal)
        self._update_enclosures(removal, EnclosureType.REMOVAL)
        self._append_token(new_token)

    def visit_broken_away(self, broken_away: BrokenAway) -> None:
        new_token = self._set_enclosure_type(broken_away)
        self._update_enclosures(broken_away, EnclosureType.BROKEN_AWAY)
        self._append_token(new_token)

    def visit_perhaps_broken_away(self, broken_away: PerhapsBrokenAway) -> None:
        new_token = self._set_enclosure_type(broken_away)
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if EnclosureType.BROKEN_AWAY in self._enclosures
            else EnclosureType.PERHAPS
        )
        self._update_enclosures(broken_away, perhaps_type)
        self._append_token(new_token)

    def visit_document_oriented_gloss(self, gloss: DocumentOrientedGloss) -> None:
        new_token = self._set_enclosure_type(gloss)
        self._update_enclosures(gloss, EnclosureType.DOCUMENT_ORIENTED_GLOSS)
        self._append_token(new_token)

    def visit_emendation(self, emendation: Emendation) -> None:
        new_token = self._set_enclosure_type(emendation)
        self._update_enclosures(emendation, EnclosureType.EMENDATION)
        self._append_token(new_token)

    def _visit_parts(self, tokens: Sequence[Token]) -> Sequence[Token]:
        part_visitor = EnclosureUpdater(self._enclosures)
        for token in (token for token in tokens if hasattr(token, "accept")):
            token.accept(part_visitor)

        self._enclosures = part_visitor._enclosures

        return part_visitor.tokens

    def _update_enclosures(self, token: Enclosure, enclosure: EnclosureType):
        self._enclosures = (
            self._enclosures.union({enclosure})
            if token.is_open
            else self._enclosures.difference({enclosure})
        )


def set_enclosure_type(
    tokens: Union[Sequence[Token], Iterable[Token]],
) -> Sequence[Token]:
    enclosure_visitor = EnclosureUpdater()
    for token in tokens:
        token.accept(enclosure_visitor)

    return enclosure_visitor.tokens
