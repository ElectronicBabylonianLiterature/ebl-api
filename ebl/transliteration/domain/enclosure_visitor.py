from enum import Enum, unique
from functools import singledispatchmethod  # type: ignore
from typing import AbstractSet, FrozenSet, Set

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Gloss,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.sign_tokens import NamedSign
from ebl.transliteration.domain.tokens import (
    Variant,
    Token,
    TokenVisitor,
)
from ebl.transliteration.domain.word_tokens import Word


@unique
class EnclosureType(Enum):
    ACCIDENTAL_OMISSION = (
        "ACCIDENTAL_OMISSION",
        frozenset(["INTENTIONAL_OMISSION"]),
    )
    INTENTIONAL_OMISSION = (
        "INTENTIONAL_OMISSION",
        frozenset(["ACCIDENTAL_OMISSION"]),
    )
    REMOVAL = ("REMOVAL",)
    BROKEN_AWAY = (
        "BROKEN_AWAY",
        frozenset(["PERHAPS_BROKEN_AWAY", "PERHAPS"]),
    )
    PERHAPS_BROKEN_AWAY = (
        "PERHAPS_BROKEN_AWAY",
        frozenset(["PERHAPS", "ACCIDENTAL_OMISSION", "INTENTIONAL_OMISSION",]),
        frozenset(["BROKEN_AWAY"]),
    )
    PERHAPS = (
        "PERHAPS",
        frozenset(
            [
                "PERHAPS_BROKEN_AWAY",
                "BROKEN_AWAY",
                "ACCIDENTAL_OMISSION",
                "INTENTIONAL_OMISSION",
            ]
        ),
    )
    DOCUMENT_ORIENTED_GLOSS = ("DOCUMENT_ORIENTED_GLOSS",)

    def __init__(
        self,
        id_: str,
        forbidden: FrozenSet[str] = frozenset(),
        required: FrozenSet[str] = frozenset(),
    ):
        self._id = id_
        self._forbidden = forbidden.union({id_})
        self._required = required

    @property
    def required(self) -> Set["EnclosureType"]:
        return {EnclosureType[name] for name in self._required}

    @property
    def forbidden(self) -> Set["EnclosureType"]:
        return {EnclosureType[name] for name in self._forbidden}

    def does_not_forbid(self, enclosures: AbstractSet["EnclosureType"]) -> bool:
        return self.forbidden.isdisjoint(enclosures)

    def are_requirements_satisfied_by(
        self, enclosures: AbstractSet["EnclosureType"]
    ) -> bool:
        return self.required.issubset(enclosures)


class EnclosureVisitorState:
    def __init__(self, initial: AbstractSet[EnclosureType] = frozenset()):
        self._enclosures: Set[EnclosureType] = set(initial)

    @property
    def enclosures(self) -> FrozenSet[EnclosureType]:
        return frozenset(self._enclosures)

    @property
    def has_enclosures(self) -> int:
        return len(self._enclosures) > 0

    def is_open(self, enclosure: EnclosureType) -> bool:
        return enclosure in self._enclosures

    def open(self, enclosure: EnclosureType) -> None:
        if self._is_allowed_to_open(enclosure):
            self._enclosures.add(enclosure)
        else:
            raise EnclosureError()

    def close(self, enclosure: EnclosureType) -> None:
        if self._is_allowed_to_close(enclosure):
            self._enclosures.remove(enclosure)
        else:
            raise EnclosureError()

    def _is_allowed_to_open(self, enclosure: EnclosureType) -> bool:
        return enclosure.does_not_forbid(
            self._enclosures
        ) and enclosure.are_requirements_satisfied_by(self._enclosures)

    def _is_allowed_to_close(self, enclosure: EnclosureType) -> bool:
        return self.is_open(enclosure) and not self._is_required(enclosure)

    def _is_required(self, enclosure: EnclosureType) -> bool:
        required = {
            required_type
            for open_ in self._enclosures
            for required_type in open_.required
        }
        return enclosure in required


class EnclosureVisitor(TokenVisitor):
    def __init__(self, initial: AbstractSet[EnclosureType] = frozenset()):
        self._enclosures = EnclosureVisitorState(initial)

    @property
    def enclosures(self) -> AbstractSet[EnclosureType]:
        return self._enclosures.enclosures

    def done(self):
        if self._enclosures.has_enclosures:
            raise EnclosureError()

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        pass

    @visit.register
    def _visit_variant(self, token: Variant) -> None:
        def sub_visit(sub_token: Token) -> AbstractSet[EnclosureType]:
            sub_visitor = EnclosureVisitor(self._enclosures.enclosures)
            sub_token.accept(sub_visitor)
            return sub_visitor.enclosures

        results = set(map(sub_visit, token.tokens))

        if len(results) == 1:
            self._enclosures = EnclosureVisitorState(results.pop())
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
        if token == AccidentalOmission.open():
            self._enclosures.open(EnclosureType.ACCIDENTAL_OMISSION)
        else:
            self._enclosures.close(EnclosureType.ACCIDENTAL_OMISSION)

    @visit.register
    def _visit_intentional_omission(self, token: IntentionalOmission) -> None:
        if token == IntentionalOmission.open():
            self._enclosures.open(EnclosureType.INTENTIONAL_OMISSION)
        else:
            self._enclosures.close(EnclosureType.INTENTIONAL_OMISSION)

    @visit.register
    def _visit_removal(self, token: Removal) -> None:
        if token == Removal.open():
            self._enclosures.open(EnclosureType.REMOVAL)
        else:
            self._enclosures.close(EnclosureType.REMOVAL)

    @visit.register
    def _visit_broken_away(self, token: BrokenAway) -> None:
        if token == BrokenAway.open():
            self._enclosures.open(EnclosureType.BROKEN_AWAY)
        else:
            self._enclosures.close(EnclosureType.BROKEN_AWAY)

    @visit.register
    def _visit_perhaps_broken_away(self, token: PerhapsBrokenAway) -> None:
        perhaps_type = (
            EnclosureType.PERHAPS_BROKEN_AWAY
            if self._enclosures.is_open(EnclosureType.BROKEN_AWAY)
            else EnclosureType.PERHAPS
        )
        if token == PerhapsBrokenAway.open():
            self._enclosures.open(perhaps_type)
        else:
            self._enclosures.close(perhaps_type)

    @visit.register
    def _visit_document_oriented_gloss(self, token: DocumentOrientedGloss) -> None:
        if token == DocumentOrientedGloss.open():
            self._enclosures.open(EnclosureType.DOCUMENT_ORIENTED_GLOSS)
        else:
            self._enclosures.close(EnclosureType.DOCUMENT_ORIENTED_GLOSS)
